# Smart HTTP for one bare repository, using only what the pinned Git image contains.
# Each connection is a child process that hands its socket to git's own pack programs.
use strict;
use warnings;
use IO::Socket::INET;
use IO::Uncompress::Gunzip qw(gunzip);

my $repo  = '/repos/dispatch.git';
my $limit = 64 * 1024 * 1024;

unless (-d $repo) {
    system('git', 'init', '--quiet', '--bare', '--initial-branch=main', $repo) == 0
      or die "could not create the repository\n";
}
$SIG{CHLD} = 'IGNORE';
my $server = IO::Socket::INET->new(LocalPort => 8080, Listen => 64, ReuseAddr => 1)
  or die "could not listen: $!\n";
while (my $client = $server->accept) {
    my $child = fork;
    if (defined $child && $child == 0) {
        # git waits for its own helpers, so it must not inherit the ignored signal.
        $SIG{CHLD} = 'DEFAULT';
        serve($client);
        exit 0;
    }
    close $client;
}

sub reply {
    my ($client, $status, $type, $body) = @_;
    print $client "HTTP/1.1 $status\r\nContent-Type: $type\r\n",
      "Cache-Control: no-cache\r\nConnection: close\r\n\r\n", $body;
}

sub refuse {
    my ($client, $status) = @_;
    reply($client, $status, 'text/plain', "$status\n");
}

# Runs one of git's pack programs with the socket as its output.
sub hand_over {
    my ($client, @command) = @_;
    open STDOUT, '>&', $client or exit 1;
    exec 'git', @command, $repo;
    exit 1;
}

sub serve {
    my $client = shift;
    binmode $client;
    $client->autoflush(1);
    my $line = <$client> // return;
    my ($method, $target) = $line =~ m{^(GET|POST) (\S+) HTTP/1\.[01]\r?\n$}
      or return refuse($client, '400 Bad Request');
    my %header;
    while (defined(my $field = <$client>)) {
        last if $field =~ /^\r?\n$/;
        $header{lc $1} = $2 if $field =~ /^([^:\s]+):\s*(.*?)\r?\n$/;
    }
    my ($path, $query) = split /\?/, $target, 2;
    my ($what) = $path =~ m{^/cgi-bin/git/dispatch\.git/(info/refs|git-upload-pack|git-receive-pack)$}
      or return refuse($client, '404 Not Found');
    my $protocol = $header{'git-protocol'} // '';
    $ENV{GIT_PROTOCOL} = $protocol if $protocol =~ /^[\w=:.-]+$/;

    if ($what eq 'info/refs') {
        my ($kind) = ($query // '') =~ /^service=git-(upload|receive)-pack$/;
        return refuse($client, '400 Bad Request') unless $method eq 'GET' && $kind;
        my $service = "$kind-pack";
        my $banner  = "# service=git-$service\n";
        # Protocol version 2 starts with the capability list, without the service banner.
        my $preamble = $service eq 'upload-pack' && $protocol =~ /version=2/
          ? ''
          : sprintf('%04x', length($banner) + 4) . $banner . '0000';
        reply($client, '200 OK', "application/x-git-$service-advertisement", $preamble);
        hand_over($client, $service, '--stateless-rpc', '--advertise-refs');
    }

    return refuse($client, '405 Method Not Allowed') unless $method eq 'POST';
    (my $service = $what) =~ s/^git-//;
    print $client "HTTP/1.1 100 Continue\r\n\r\n"
      if lc($header{expect} // '') eq '100-continue';
    my $body = '';
    if (lc($header{'transfer-encoding'} // '') eq 'chunked') {
        while (defined(my $size = <$client>)) {
            $size =~ s/[;\s].*//s;
            my $length = hex $size;
            last unless $length;
            return refuse($client, '413 Content Too Large') if length($body) + $length > $limit;
            read($client, my $chunk, $length) == $length or return;
            $body .= $chunk;
            <$client>;
        }
    }
    else {
        my $length = $header{'content-length'} // 0;
        return refuse($client, '400 Bad Request') unless $length =~ /^\d+$/;
        return refuse($client, '413 Content Too Large') if $length > $limit;
        if ($length) { read($client, $body, $length) == $length or return }
    }
    if (($header{'content-encoding'} // '') =~ /gzip/) {
        my $plain;
        gunzip(\$body => \$plain) or return refuse($client, '400 Bad Request');
        $body = $plain;
    }
    open my $request, '+>', undef or return refuse($client, '500 Internal Server Error');
    print $request $body;
    seek $request, 0, 0;
    reply($client, '200 OK', "application/x-git-$service-result", '');
    open STDIN, '<&', $request or exit 1;
    hand_over($client, $service, '--stateless-rpc');
}
