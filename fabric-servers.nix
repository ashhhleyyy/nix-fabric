{ callPackage
, lib

, javaPackages
}:

let
  versions = lib.importJSON ./versions.json;

  escapeVersion = builtins.replaceStrings [ "." ] [ "_" ];
  getJavaVersion = v: (builtins.getAttr "openjdk${toString v}" javaPackages.compiler).headless;

  packages = lib.mapAttrs'
    (version: value: {
      name = escapeVersion version;
      value = callPackage ./fabric-server.nix {
        inherit (value) mainClass libraries;
        inherit (versions) fabricLoaderVersion;
        
        minecraftVersion = version;

        jdk_headless = getJavaVersion value.vanillaJar.javaVersion;

        serverJarUrl = value.vanillaJar.url;
        serverJarSha1 = value.vanillaJar.sha1;
      };
    })
    versions.versions;
in
lib.recurseIntoAttrs packages
