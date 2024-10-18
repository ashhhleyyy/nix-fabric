{ lib
, callPackage
, fetchurl
, writeShellApplication

, udev
, jdk_headless

, minecraftVersion
, fabricLoaderVersion

, serverJarUrl
, serverJarSha1

, mainClass
, libraries

, extraJvmArgs ? []
, fabricMods ? []
}:

let
  fetchLib = library: fetchurl {
    url = library.url;
    hash = library.sha256;
  };
  officialServerJar = fetchurl {
    url = serverJarUrl;
    sha1 = serverJarSha1;

    meta = with lib; {
      sourceProvenance = with sourceTypes; [ binaryBytecode ];
      license = licenses.unfreeRedistributable;
    };
  };
  classPath = lib.concatStringsSep ":" (map fetchLib libraries);
  modList = lib.concatStringsSep ":" fabricMods;
in

writeShellApplication {
  name = "fabric-server";

  runtimeInputs = [ jdk_headless ];

  text = ''
  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${lib.makeLibraryPath [udev]}
  export LD_LIBRARY_PATH

  exec java -Dfabric.gameJarPath=${officialServerJar} \
    -Dfabric.addMods=${modList} \
    ${lib.escapeShellArgs extraJvmArgs} \
    -cp ${classPath} \
    ${mainClass} \
    nogui
  '';
}
