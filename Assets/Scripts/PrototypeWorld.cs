using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class PrototypeWorld : MonoBehaviour
{
    private sealed class Resident
    {
        public string name;
        public int hunger;
        public GameObject visual;
    }

    [System.Serializable]
    private sealed class ProgressSave
    {
        public int version = 1;
        public int day;
        public int fruit;
        public int wood;
        public int beds;
        public int gardens;
        public int morale;
        public float dayClock;
        public List<int> hunger;
        public List<bool> depleted;
    }

    private const string SaveKey = "BosqueVivo.Prototype.Progress.v1";
    private const float DayDuration = 100f;

    private readonly List<Resident> residents = new List<Resident>();
    private readonly List<ResourcePickup> resources = new List<ResourcePickup>();
    private Camera playerCamera;
    private int day = 1;
    private int fruit = 5;
    private int wood = 3;
    private int beds = 2;
    private int gardens;
    private int morale = 100;
    private float dayClock = DayDuration;
    private string message = "Alimente a família, prepare as camas e atravesse a noite.";
    private bool ended;
    private Light sunlight;
    private GUIStyle heading;
    private GUIStyle body;

    private void Start()
    {
        ProgressSave saved = LoadProgress();
        if (saved != null)
        {
            day = saved.day;
            fruit = saved.fruit;
            wood = saved.wood;
            beds = saved.beds;
            gardens = saved.gardens;
            morale = saved.morale;
            dayClock = saved.dayClock;
            ended = day >= 7 || morale == 0;
            message = ended ? (morale == 0 ? "A comunidade perdeu todo o ânimo." : "Vitória! A comunidade chegou ao dia 7.") :
                "Partida recuperada. Confira as necessidades antes de passar a noite.";
        }

        RenderSettings.ambientLight = new Color(0.58f, 0.65f, 0.59f);
        CreateBox("Solo", new Vector3(0f, -0.3f, 0f), new Vector3(48f, 0.6f, 48f), new Color(0.34f, 0.53f, 0.32f));
        CreateBox("Clareira", new Vector3(0f, 0.01f, 2f), new Vector3(11f, 0.03f, 11f), new Color(0.58f, 0.51f, 0.35f));

        GameObject lightObject = new GameObject("Sol");
        sunlight = lightObject.AddComponent<Light>();
        sunlight.type = LightType.Directional;
        sunlight.intensity = 1.2f;
        lightObject.transform.rotation = Quaternion.Euler(45f, -25f, 0f);

        GameObject player = new GameObject("Guardião");
        player.transform.position = new Vector3(0f, 1.1f, -7f);
        CharacterController controller = player.AddComponent<CharacterController>();
        controller.height = 1.8f;
        controller.radius = 0.35f;
        controller.center = new Vector3(0f, 0.9f, 0f);
        GameObject cameraObject = new GameObject("Olhos do guardião");
        cameraObject.transform.SetParent(player.transform, false);
        cameraObject.transform.localPosition = new Vector3(0f, 0.8f, 0f);
        playerCamera = cameraObject.AddComponent<Camera>();
        playerCamera.tag = "MainCamera";
        playerCamera.clearFlags = CameraClearFlags.SolidColor;
        playerCamera.backgroundColor = new Color(0.65f, 0.80f, 0.86f);
        player.AddComponent<FirstPersonWalker>().view = playerCamera;

        if (saved != null)
        {
            foreach (int hunger in saved.hunger) AddResident(hunger);
        }
        else for (int i = 0; i < 3; i++) AddResident();
        for (int i = 0; i < beds; i++) DrawBed(i);
        for (int i = 0; i < gardens; i++) DrawGarden(i);

        AddResource(ResourcePickup.Kind.Wood, new Vector3(-5f, 0f, 0f), 3);
        AddResource(ResourcePickup.Kind.Wood, new Vector3(-8f, 0f, 5f), 3);
        AddResource(ResourcePickup.Kind.Wood, new Vector3(7f, 0f, 4f), 3);
        AddResource(ResourcePickup.Kind.Fruit, new Vector3(4f, 0f, -2f), 4);
        AddResource(ResourcePickup.Kind.Fruit, new Vector3(-4f, 0f, -3f), 4);
        AddResource(ResourcePickup.Kind.Fruit, new Vector3(7f, 0f, -7f), 4);
        if (saved != null)
        {
            for (int i = 0; i < resources.Count; i++)
                if (saved.depleted[i]) resources[i].Harvest();
        }
        CreateScenery();
        UpdateLighting();

        if (ended) FreezePlayer();
    }

    private void Update()
    {
        if (ended)
        {
            if (Input.GetKeyDown(KeyCode.R)) Restart();
            return;
        }
        if (Cursor.lockState != CursorLockMode.Locked) return;

        dayClock -= Time.deltaTime;
        UpdateLighting();
        if (Input.GetKeyDown(KeyCode.E)) HarvestTarget();
        if (Input.GetKeyDown(KeyCode.F)) FeedResidents();
        if (Input.GetKeyDown(KeyCode.B)) BuildBed();
        if (Input.GetKeyDown(KeyCode.G)) BuildGarden();
        if (Input.GetKeyDown(KeyCode.N) || dayClock <= 0f) EndDay();
    }

    private void HarvestTarget()
    {
        ResourcePickup target = GetTarget();
        if (target == null)
        {
            message = "Aproxime-se de uma árvore ou moita e mire no recurso.";
            return;
        }

        int collected = target.Harvest();
        if (collected <= 0) return;
        if (target.kind == ResourcePickup.Kind.Wood) wood += collected;
        else fruit += collected;
        message = "+" + collected + (target.kind == ResourcePickup.Kind.Wood ? " madeiras." : " frutas.");
        SaveProgress();
    }

    private ResourcePickup GetTarget()
    {
        if (playerCamera == null) return null;
        Ray ray = new Ray(playerCamera.transform.position, playerCamera.transform.forward);
        RaycastHit hit;
        if (!Physics.Raycast(ray, out hit, 4f)) return null;
        return hit.collider.GetComponentInParent<ResourcePickup>();
    }

    private void FeedResidents()
    {
        int fed = 0;
        foreach (Resident resident in residents)
        {
            if (resident.hunger == 0 || fruit == 0) continue;
            resident.hunger = 0;
            TintResident(resident);
            fruit--;
            fed++;
        }

        message = fed > 0 ? "Você alimentou " + fed + " morador(es)." :
            fruit == 0 ? "Faltam frutas. Procure as moitas coloridas." : "Todos estão alimentados.";
        if (fed > 0) SaveProgress();
    }

    private void BuildBed()
    {
        if (wood < 3)
        {
            message = "Uma cama custa 3 madeiras. Procure as árvores.";
            return;
        }

        if (beds >= residents.Count)
        {
            message = "Já existe uma cama para cada morador.";
            return;
        }

        wood -= 3;
        DrawBed(beds);
        beds++;
        message = "Nova cama construída!";
        SaveProgress();
    }

    private void BuildGarden()
    {
        if (gardens >= 3)
        {
            message = "A clareira já tem três hortas.";
            return;
        }
        if (wood < 4)
        {
            message = "Uma horta custa 4 madeiras e produz 3 frutas por manhã.";
            return;
        }

        wood -= 4;
        DrawGarden(gardens);
        gardens++;
        message = "Horta pronta! Ela produzirá 3 frutas na próxima manhã.";
        SaveProgress();
    }

    private void EndDay()
    {
        int hungry = 0;
        foreach (Resident resident in residents)
        {
            resident.hunger = Mathf.Min(3, resident.hunger + 1);
            TintResident(resident);
            if (resident.hunger >= 3) hungry++;
        }

        int unsheltered = Mathf.Max(0, residents.Count - beds);
        int penalty = hungry * 15 + unsheltered * 8;
        morale = Mathf.Max(0, morale - penalty);
        day++;
        dayClock = DayDuration;

        if (morale == 0)
        {
            message = "A comunidade perdeu todo o ânimo. Tente novamente.";
            ended = true;
        }
        else if (day >= 7)
        {
            message = "Vitória! Sua comunidade prosperou até o sétimo dia.";
            ended = true;
        }
        else
        {
            fruit += gardens * 3;
            foreach (ResourcePickup resource in resources) resource.Regrow();
            if (morale >= 50) AddResident();
            message = "Dia " + day + ": " + hungry + " com muita fome, " + unsheltered +
                " sem cama. Ânimo -" + penalty + "; hortas +" + (gardens * 3) + " frutas.";
        }

        if (ended) FreezePlayer();
        UpdateLighting();
        SaveProgress();
    }

    private void AddResident(int startingHunger = 1)
    {
        int index = residents.Count;
        Resident member = new Resident { name = "Lume " + (index + 1), hunger = startingHunger };
        residents.Add(member);
        int column = index % 7;
        int row = index / 7;
        Vector3 position = new Vector3(-3.2f + column * 1.05f, 0.65f, 3.2f + row * 1.25f);
        GameObject resident = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        resident.name = "Lume " + (index + 1);
        member.visual = resident;
        resident.transform.position = position;
        resident.transform.localScale = Vector3.one * 0.8f;
        SetColor(resident, startingHunger >= 2 ? new Color(0.82f, 0.45f, 0.37f) :
            new Color(0.92f, 0.79f - (index % 3) * 0.13f, 0.40f));
        resident.AddComponent<ResidentVisual>().phase = index * 0.8f;
        GameObject glow = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        glow.name = "Núcleo luminoso";
        glow.transform.SetParent(resident.transform, false);
        glow.transform.localPosition = new Vector3(0f, 0.17f, -0.43f);
        glow.transform.localScale = Vector3.one * 0.23f;
        Destroy(glow.GetComponent<Collider>());
        SetColor(glow, new Color(1f, 0.97f, 0.72f));
    }

    private void DrawBed(int index)
    {
        int column = index % 7;
        int row = index / 7;
        CreateBox("Cama " + (index + 1),
            new Vector3(-3.2f + column * 1.05f, 0.14f, 5.2f + row * 1.3f),
            new Vector3(0.85f, 0.25f, 0.85f), new Color(0.36f, 0.30f, 0.48f));
    }

    private void DrawGarden(int index)
    {
        Vector3 center = new Vector3(-6f + index * 2.1f, 0.12f, -9f);
        CreateBox("Horta " + (index + 1), center, new Vector3(1.6f, 0.24f, 1.3f),
            new Color(0.45f, 0.28f, 0.17f));
        for (int i = 0; i < 3; i++)
        {
            GameObject sprout = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            sprout.name = "Broto";
            sprout.transform.position = center + new Vector3(-0.45f + 0.45f * i, 0.28f, 0f);
            sprout.transform.localScale = Vector3.one * 0.27f;
            SetColor(sprout, new Color(0.33f, 0.68f, 0.31f));
        }
    }

    private void CreateScenery()
    {
        Vector3[] stones = {
            new Vector3(-10f, 0.2f, -8f), new Vector3(9f, 0.2f, 8f),
            new Vector3(-9f, 0.2f, 9f), new Vector3(10f, 0.2f, -5f)
        };
        foreach (Vector3 position in stones)
        {
            GameObject stone = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            stone.name = "Pedra da clareira";
            stone.transform.position = position;
            stone.transform.localScale = new Vector3(1.5f, 0.55f, 1f);
            SetColor(stone, new Color(0.44f, 0.49f, 0.47f));
        }

        CreateBox("Marco da comunidade", new Vector3(1.6f, 0.6f, 0.8f),
            new Vector3(0.3f, 1.2f, 0.3f), new Color(0.42f, 0.30f, 0.17f));
        GameObject beacon = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        beacon.name = "Luz da comunidade";
        beacon.transform.position = new Vector3(1.6f, 1.4f, 0.8f);
        beacon.transform.localScale = Vector3.one * 0.7f;
        SetColor(beacon, new Color(1f, 0.85f, 0.52f));
    }

    private static void TintResident(Resident resident)
    {
        if (resident.visual == null) return;
        resident.visual.GetComponent<Renderer>().material.color = resident.hunger >= 2 ?
            new Color(0.82f, 0.45f, 0.37f) : new Color(0.92f, 0.76f, 0.40f);
    }

    private void UpdateLighting()
    {
        float daylight = Mathf.Clamp01(dayClock / DayDuration);
        if (sunlight != null) sunlight.intensity = Mathf.Lerp(0.35f, 1.15f, daylight);
        if (playerCamera != null) playerCamera.backgroundColor = Color.Lerp(
            new Color(0.21f, 0.28f, 0.42f), new Color(0.65f, 0.80f, 0.86f), daylight);
    }

    private void SaveProgress()
    {
        if (residents.Count == 0 || resources.Count != 6) return;
        ProgressSave save = new ProgressSave
        {
            day = day, fruit = fruit, wood = wood, beds = beds,
            gardens = gardens, morale = morale, dayClock = Mathf.Clamp(dayClock, 0.1f, DayDuration),
            hunger = new List<int>(), depleted = new List<bool>()
        };
        foreach (Resident resident in residents) save.hunger.Add(resident.hunger);
        foreach (ResourcePickup resource in resources) save.depleted.Add(!resource.available);
        PlayerPrefs.SetString(SaveKey, JsonUtility.ToJson(save));
        PlayerPrefs.Save();
    }

    private static ProgressSave LoadProgress()
    {
        if (!PlayerPrefs.HasKey(SaveKey)) return null;
        try
        {
            ProgressSave save = JsonUtility.FromJson<ProgressSave>(PlayerPrefs.GetString(SaveKey));
            if (save == null || save.version != 1 || save.day < 1 || save.day > 7 ||
                save.hunger == null || save.hunger.Count < 3 || save.hunger.Count > 12 ||
                save.depleted == null || save.depleted.Count != 6 ||
                save.beds < 0 || save.beds > 12 || save.gardens < 0 || save.gardens > 3 ||
                save.fruit < 0 || save.fruit > 9999 || save.wood < 0 || save.wood > 9999 ||
                save.morale < 0 || save.morale > 100 ||
                float.IsNaN(save.dayClock) || float.IsInfinity(save.dayClock) ||
                save.dayClock <= 0f || save.dayClock > DayDuration) return null;
            foreach (int hunger in save.hunger) if (hunger < 0 || hunger > 3) return null;
            return save;
        }
        catch (System.Exception)
        {
            return null;
        }
    }

    private void OnApplicationPause(bool paused)
    {
        if (paused) SaveProgress();
    }

    private void OnApplicationQuit()
    {
        SaveProgress();
    }

    private void Restart()
    {
        PlayerPrefs.DeleteKey(SaveKey);
        PlayerPrefs.Save();
        SceneManager.LoadScene(SceneManager.GetActiveScene().name);
    }

    private void FreezePlayer()
    {
        FirstPersonWalker walker = playerCamera.GetComponentInParent<FirstPersonWalker>();
        if (walker != null) walker.enabled = false;
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }

    private void AddResource(ResourcePickup.Kind kind, Vector3 position, int amount)
    {
        GameObject root = new GameObject(kind == ResourcePickup.Kind.Wood ? "Árvore" : "Moita de frutas");
        root.transform.position = position;
        ResourcePickup pickup = root.AddComponent<ResourcePickup>();
        pickup.kind = kind;
        pickup.amount = amount;
        resources.Add(pickup);

        if (kind == ResourcePickup.Kind.Wood)
        {
            CreateBox("Tronco", position + Vector3.up * 1.15f, new Vector3(0.8f, 2.3f, 0.8f),
                new Color(0.48f, 0.27f, 0.13f)).transform.SetParent(root.transform, true);
            GameObject leaves = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            leaves.name = "Copa";
            leaves.transform.position = position + Vector3.up * 2.5f;
            leaves.transform.localScale = new Vector3(2.5f, 2.1f, 2.5f);
            leaves.transform.SetParent(root.transform, true);
            SetColor(leaves, new Color(0.19f, 0.42f, 0.25f));
        }
        else
        {
            GameObject bush = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            bush.name = "Frutas";
            bush.transform.position = position + Vector3.up * 0.6f;
            bush.transform.localScale = new Vector3(1.4f, 1.15f, 1.4f);
            bush.transform.SetParent(root.transform, true);
            SetColor(bush, new Color(0.76f, 0.24f, 0.32f));
        }
    }

    private static GameObject CreateBox(string name, Vector3 position, Vector3 scale, Color color)
    {
        GameObject box = GameObject.CreatePrimitive(PrimitiveType.Cube);
        box.name = name;
        box.transform.position = position;
        box.transform.localScale = scale;
        SetColor(box, color);
        return box;
    }

    private static void SetColor(GameObject obj, Color color)
    {
        Shader shader = Shader.Find("Standard");
        if (shader == null) shader = Shader.Find("Universal Render Pipeline/Lit");
        Material material = new Material(shader);
        material.color = color;
        obj.GetComponent<Renderer>().material = material;
    }

    private void OnGUI()
    {
        if (heading == null)
        {
            heading = new GUIStyle(GUI.skin.label) { fontSize = 20, fontStyle = FontStyle.Bold };
            heading.normal.textColor = Color.white;
            body = new GUIStyle(GUI.skin.label) { fontSize = 15, wordWrap = true };
            body.normal.textColor = Color.white;
        }

        float scale = Mathf.Max(0.55f, Mathf.Min(1f, Mathf.Min(Screen.width / 1024f, Screen.height / 640f)));
        Matrix4x4 previousMatrix = GUI.matrix;
        GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
        float width = Screen.width / scale;
        float height = Screen.height / scale;

        int hungryTonight = 0;
        foreach (Resident resident in residents) if (resident.hunger >= 2) hungryTonight++;
        int missingBeds = Mathf.Max(0, residents.Count - beds);
        int predictedLoss = hungryTonight * 15 + missingBeds * 8;

        GUI.Box(new Rect(12, 12, 430, 190), "");
        GUI.Label(new Rect(24, 20, 395, 32), "BOSQUE VIVO   ·   DIA " + day + "/7", heading);
        GUI.Label(new Rect(24, 56, 395, 25), "Moradores: " + residents.Count + "  |  Camas: " + beds + "  |  Ânimo: " + morale, body);
        GUI.Label(new Rect(24, 82, 395, 25), "Frutas: " + fruit + "  |  Madeiras: " + wood + "  |  Hortas: " + gardens, body);
        GUI.Label(new Rect(24, 108, 395, 25), "Anoitece em " + Mathf.CeilToInt(dayClock) + "s", body);
        GUI.color = new Color(0.30f, 0.73f, 0.50f);
        GUI.DrawTexture(new Rect(24, 140, 390f * Mathf.Clamp01(dayClock / DayDuration), 7), Texture2D.whiteTexture);
        GUI.color = Color.white;
        GUI.Label(new Rect(24, 150, 395, 48), message, body);

        GUI.Box(new Rect(12, 212, 430, 82), "");
        GUI.Label(new Rect(24, 220, 390, 30), "PRÓXIMA NOITE", heading);
        GUI.Label(new Rect(24, 252, 395, 38), hungryTonight + " com fome grave  ·  " + missingBeds +
            " sem cama  ·  Ânimo -" + predictedLoss, body);

        GUI.Box(new Rect(12, height - 111, 600, 98), "");
        GUI.Label(new Rect(24, height - 102, 570, 83),
            "WASD: andar  ·  Shift: correr  ·  Mouse: olhar  ·  E: colher\n" +
            "F: alimentar  ·  B: cama (3 madeiras)  ·  G: horta (4 madeiras)\n" +
            "N: passar a noite  ·  Esc: cursor", body);

        if (ended)
        {
            GUI.Box(new Rect(width / 2f - 245f, height / 2f - 72f, 490f, 145f), "");
            GUI.Label(new Rect(width / 2f - 220f, height / 2f - 51f, 440f, 70f), message, heading);
            if (GUI.Button(new Rect(width / 2f - 140f, height / 2f + 20f, 280f, 35f),
                    "Recomeçar (R)")) Restart();
        }
        else if (Cursor.lockState == CursorLockMode.Locked)
        {
            GUI.Label(new Rect(width / 2f - 5f, height / 2f - 15f, 30f, 30f), "+", heading);
            ResourcePickup target = GetTarget();
            if (target != null)
            {
                GUI.Box(new Rect(width / 2f - 110f, height / 2f + 26f, 220f, 30f),
                    "E  ·  " + (target.kind == ResourcePickup.Kind.Wood ? "Coletar madeira" : "Colher frutas"));
            }
        }
        GUI.matrix = previousMatrix;
    }
}
