"""Serving CSR approval must remain inside recorded node identities and addresses."""

import base64
import ipaddress

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from dockyard.runtimes.metrics import valid_serving_request


def request(
    *,
    common_name="system:node:dockyard-owned-worker",
    ip="172.20.0.3",
    dns="dockyard-owned-worker",
    organization="system:nodes",
):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                    x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                ]
            )
        )
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName(dns),
                    x509.IPAddress(ipaddress.ip_address(ip)),
                ]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    return {
        "spec": {
            "username": "system:node:dockyard-owned-worker",
            "signerName": "kubernetes.io/kubelet-serving",
            "usages": ["digital signature", "key encipherment", "server auth"],
            "request": base64.b64encode(csr.public_bytes(serialization.Encoding.PEM)).decode(),
        }
    }


NODES = {
    "dockyard-owned-worker": {
        "status": {
            "addresses": [
                {"type": "InternalIP", "address": "172.20.0.3"},
                {"type": "Hostname", "address": "dockyard-owned-worker"},
            ]
        }
    }
}


def test_accepts_a_signed_request_for_the_owned_node_addresses():
    assert valid_serving_request(request(), NODES)


@pytest.mark.parametrize(
    "changes",
    [
        {"common_name": "system:node:another-node"},
        {"organization": "system:masters"},
        {"ip": "127.0.0.1"},
        {"dns": "kubernetes.default.svc"},
    ],
)
def test_rejects_identity_or_address_expansion(changes):
    assert not valid_serving_request(request(**changes), NODES)


def test_rejects_client_signing_and_unrecorded_nodes():
    csr = request()
    assert not valid_serving_request(csr, {})
    csr["spec"]["usages"].append("client auth")
    assert not valid_serving_request(csr, NODES)
    csr["spec"]["usages"] = ["server auth"]
    csr["spec"]["signerName"] = "kubernetes.io/kube-apiserver-client"
    assert not valid_serving_request(csr, NODES)


def test_rejects_a_request_with_a_broken_signature():
    csr = request()
    pem = base64.b64decode(csr["spec"]["request"])
    parsed = x509.load_pem_x509_csr(pem)
    der = bytearray(parsed.public_bytes(serialization.Encoding.DER))
    der[-1] ^= 1
    damaged = x509.load_der_x509_csr(bytes(der))
    csr["spec"]["request"] = base64.b64encode(
        damaged.public_bytes(serialization.Encoding.PEM)
    ).decode()
    assert not valid_serving_request(csr, NODES)
