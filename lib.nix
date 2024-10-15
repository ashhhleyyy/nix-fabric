{
  fetchModrinth = { projectId, versionId, fileName, sha256 }: builtins.fetchurl {
    url = "https://cdn.modrinth.com/data/${projectId}/versions/${versionId}/${fileName}";
    inherit sha256;
  };
}
