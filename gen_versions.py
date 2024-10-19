import base64
import functools
import json
import re
import requests
import urllib

V2_VERSIONS_GAME = 'https://meta.fabricmc.net/v2/versions/game'
V2_VERSIONS_LOADER_SERVER_JSON = 'https://meta.fabricmc.net/v2/versions/loader/{game_version}/{loader_version}/server/json'
LAUNCHER_MANIFEST = 'https://launchermeta.mojang.com/mc/game/version_manifest_v2.json'
EXPERIMENTAL_LAUNCHER_MANIFEST = 'https://maven.fabricmc.net/net/minecraft/experimental_versions.json'
FABRIC_MAVEN = 'https://maven.fabricmc.net/'
INTERMEDIARY_NAME = 'net.fabricmc:intermediary:{game_version}:v2'

LOADER_VERSION = '0.16.7'

def fetch_launcher_manifest(manifest: str):
    resp = requests.get(manifest)
    resp.raise_for_status()
    return resp.json()

def merge_launcher_manifests():
    launcher_manifest = fetch_launcher_manifest(LAUNCHER_MANIFEST)
    experimental_launcher_manifest = fetch_launcher_manifest(EXPERIMENTAL_LAUNCHER_MANIFEST)
    full_launcher_manifest = {}
    for version in launcher_manifest['versions']:
        full_launcher_manifest[version['id']] = version
    for version in experimental_launcher_manifest['versions']:
        full_launcher_manifest[version['id']] = version
    return full_launcher_manifest

LAUNCHER_MANIFEST = merge_launcher_manifests()

def fetch_game_versions():
    print('Fetching game versions...')
    resp = requests.get(V2_VERSIONS_GAME)
    resp.raise_for_status()
    return resp.json()

def fetch_server_profile(game_version: str, loader_version: str):
    print('  Fetching server profile...')
    resp = requests.get(V2_VERSIONS_LOADER_SERVER_JSON.format(game_version=game_version, loader_version=loader_version))
    resp.raise_for_status()
    return resp.json()

def format_maven_url(base: str, name: str, extension: str='jar') -> str:
    parts = name.split(':')
    if len(parts) == 3:
        group, name, version = parts
        filename = urllib.parse.quote(f'{name}-{version}.{extension}')
    elif len(parts) == 4:
        group, name, version, classifier = parts
        filename = urllib.parse.quote(f'{name}-{version}-{classifier}.{extension}')
    else:
        raise RuntimeError(f'invalid maven object name: `{name}`')
    group = urllib.parse.quote(group).replace('.', '/')
    name = urllib.parse.quote(name)
    version = urllib.parse.quote(version)
    return base + group + '/' + name + '/' + version + '/' + filename

def create_jar_name(maven_url: str) -> str:
    return re.sub(r'[^a-zA-Z0-9-_.]', '__', maven_url)

def make_nix_hash(alg: str, hexdigest: str) -> str:
    b = bytes.fromhex(hexdigest)
    b64 = base64.b64encode(b).decode()
    return f'{alg}-{b64}'

@functools.cache
def library_info(baseUrl: str, mavenName: str, sha256: str):
    url = format_maven_url(baseUrl, mavenName)
    name = create_jar_name(url)
    if sha256:
        return {
            'url': url,
            'name': name,
            'sha256': make_nix_hash('sha256', sha256),
        }
    else:
        print(f'  Fetching library hash for {mavenName}...')
        # we need to fetch the hash
        hashUrl = url + '.sha256'
        resp = requests.get(hashUrl)
        resp.raise_for_status()
        return {
            'url': url,
            'name': name,
            'sha256': make_nix_hash('sha256', resp.text),
        }

@functools.cache
def get_vanilla_details(version: str):
    print(f'  Fetching JAR information for {version}...')
    resp = requests.get(LAUNCHER_MANIFEST[version]['url'])
    resp.raise_for_status()
    resp = resp.json()
    server = resp['downloads']['server']
    client = resp['downloads']['client']
    javaVersion = '8'
    if 'javaVersion' in resp and 'majorVersion' in resp['javaVersion']:
        javaVersion = resp['javaVersion']['majorVersion']
    return {
        'serverJar': server,
        'clientJar': client,
        'javaVersion': javaVersion,
        'manifest': {
            'url': LAUNCHER_MANIFEST[version]['url'],
            'sha1': LAUNCHER_MANIFEST[version]['sha1'],
        }
    }

def get_libraries(libraries):
    return list(map(lambda lib: library_info(lib['url'], lib['name'], lib['sha256'] if 'sha256' in lib else None), libraries))

def get_intermediary(game_version: str):
    return library_info(FABRIC_MAVEN, INTERMEDIARY_NAME.format(game_version=game_version), None)

def generate_version_info(game_version: str, loader_version: str):
    profile = fetch_server_profile(game_version, loader_version)
    vanilla  = get_vanilla_details(game_version)
    return {
        'id': profile['id'],
        'mainClass': profile['mainClass'],
        'libraries': get_libraries(profile['libraries']),
        'vanilla': vanilla,
        'intermediary': get_intermediary(game_version),
    }

def main():
    versions = fetch_game_versions()

    output_versions = {}
    latestStable = None
    latestUnstable = None
    for version in versions:
        if not latestStable and version['stable']:
            latestStable = version['version']
        elif not  latestUnstable and not version['stable']:
            latestUnstable = version['version']
        print(f'Fetching data for version {version['version']}...')
        version_data = generate_version_info(version['version'], LOADER_VERSION)
        output_versions[version['version']] = version_data
    with open('versions.json', 'w') as f:
        json.dump({
            'latest': {
                'stable': latestStable,
                'unstable': latestUnstable,
            },
            'fabricLoaderVersion': LOADER_VERSION,
            'versions': output_versions,
        }, f, indent=2)

if __name__ == '__main__':
    main()
