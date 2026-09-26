using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class CreatePrototypeScene
{
    [MenuItem("Bosque Vivo/Criar cena do protótipo")]
    private static void CreateScene()
    {
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;

        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        new GameObject("Bosque Vivo - protótipo").AddComponent<PrototypeWorld>();

        const string folder = "Assets/Scenes";
        if (!AssetDatabase.IsValidFolder(folder)) AssetDatabase.CreateFolder("Assets", "Scenes");

        const string path = "Assets/Scenes/BosqueVivo.unity";
        if (!EditorSceneManager.SaveScene(scene, path))
        {
            Debug.LogError("Não foi possível salvar a cena do protótipo.");
            return;
        }

        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(path, true) };
        AssetDatabase.Refresh();
        Debug.Log("Cena criada. Abra Assets/Scenes/BosqueVivo.unity e pressione Play.");
    }
}
