# When fetching from ftp/http/https, try here before the upstream URL
PREMIRRORS_append () {
ftp://.*/.*     http://dev.doredevelopment.dk/deif/ingredients/
http://.*/.*    http://dev.doredevelopment.dk/deif/ingredients/
https://.*/.*   http://dev.doredevelopment.dk/deif/ingredients/
}

# If upstream URL fetch fails, try here
MIRRORS_append () {
ftp://.*/.*     http://dev.doredevelopment.dk/deif/ingredients/
http://.*/.*    http://dev.doredevelopment.dk/deif/ingredients/
https://.*/.*   http://dev.doredevelopment.dk/deif/ingredients/
}
