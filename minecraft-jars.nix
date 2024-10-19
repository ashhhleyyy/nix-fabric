{ callPackage
, lib
, fetchurl

, javaPackages
}:

let
  versions = lib.importJSON ./versions.json;

  escapeVersion = builtins.replaceStrings [ "." ] [ "_" ];
  getJavaVersion = v: (builtins.getAttr "openjdk${toString v}" javaPackages.compiler).headless;
in

lib.mapAttrs'
  (version: value: {
    name = escapeVersion version;
    value = {
      client = fetchurl {
        url = value.vanilla.clientJar.url;
        sha1 = value.vanilla.clientJar.sha1;
      };
      server = fetchurl {
        url = value.vanilla.serverJar.url;
        sha1 = value.vanilla.serverJar.sha1;
      };
      manifest = fetchurl value.vanilla.manifest;
      manifest-info = value.vanilla.manifest;
      javaVersion = getJavaVersion value.vanilla.javaVersion;
      intermediary = fetchurl {
        url = value.intermediary.url;
        hash = value.intermediary.sha256;
      };
    };
  })
  versions.versions
