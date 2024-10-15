{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      overlays.default = final: prev: {
        inherit (self.packages.${prev.system}) fabric-servers;
      };
      lib = import ./lib.nix;
    } // flake-utils.lib.eachDefaultSystem(system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        scriptDeps = ps: with ps; [
          requests
        ];
      in
    {
      packages.fabric-servers = pkgs.callPackage ./fabric-servers.nix {};
      devShells.default = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [
          (python3.withPackages scriptDeps)
        ];
      };
    });
}
