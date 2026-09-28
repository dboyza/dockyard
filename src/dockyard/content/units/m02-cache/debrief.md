## Which change made the new release visible?

Editing `VERSION` changed the workspace.
Building changed the image selected by the tag.
Replacing the container made the new image serve requests.

Explain which of those three changes would be missing if the image inspection showed the new ID but the container still returned the old release.
Then predict what stopping and starting that old container would do.
A restart uses the same image; it does not follow a tag to a new image.
