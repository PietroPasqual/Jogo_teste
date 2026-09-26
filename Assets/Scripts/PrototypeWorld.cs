using System.Collections.Generic;
using UnityEngine;

public class PrototypeWorld : MonoBehaviour
{
    private sealed class Resident
    {
        public string name;
        public int hunger;
    }

    private readonly List<Resident> residents = new List<Resident>();
    private readonly List<ResourcePickup> resources = new List<ResourcePickup>();
    private Camera playerCamera;
    private int day = 1;
    private int fruit = 5;
    private int wood = 3;
    private int beds = 2;
    private int morale = 100;
    private float dayClock = 100f;
    private string message = "Alimente a família, prepare as camas e atravesse a noite.";
    private bool ended;
    private GUIStyle heading;
    private GUIStyle body;

    private void Start()
    {
        RenderSettings.ambientLight = new Color(0.58f, 0.65f, 0.59f);
        CreateBox("Solo", new Vector3(0f, -0.3f, 0f), new Vector3(48f, 0.6f, 48f), new Color(0.34f, 0.53f, 0.32f));
        CreateBox("Clareira", new Vector3(0f, 0.01f, 2f), new Vector3(11f, 0.03f, 11f), new Color(0.58f, 0.51f, 0.35f));

        GameObject lightObject = new GameObject("Sol");
        Light sunlight = lightObject.AddComponent<Light>();
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

        for (int i = 0; i < 3; i++) AddResident();
        for (int i = 0; i < beds; i++) DrawBed(i);

        AddResource(ResourcePickup.Kind.Wood, new Vector3(-5f, 0f, 0f), 3);
        AddResource(ResourcePickup.Kind.Wood, new Vector3(-8f, 0f, 5f), 3);
        AddResource(ResourcePickup.Kind.Wood, new Vector3(7f, 0f, 4f), 3);
        AddResource(ResourcePickup.Kind.Fruit, new Vector3(4f, 0f, -2f), 4);
        AddResource(ResourcePickup.Kind.Fruit, new Vector3(-4f, 0f, -3f), 4);
        AddResource(ResourcePickup.Kind.Fruit, new Vector3(7f, 0f, -7f), 4);
    }

    private void Update()
    {
        if (ended || Cursor.lockState != CursorLockMode.Locked) return;

        dayClock -= Time.deltaTime;
        if (Input.GetKeyDown(KeyCode.E)) HarvestTarget();
        if (Input.GetKeyDown(KeyCode.F)) FeedResidents();
        if (Input.GetKeyDown(KeyCode.B)) BuildBed();
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
            fruit--;
            fed++;
        }

        message = fed > 0 ? "Você alimentou " + fed + " morador(es)." :
            fruit == 0 ? "Faltam frutas. Procure as moitas coloridas." : "Todos estão alimentados.";
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
    }

    private void EndDay()
    {
        int hungry = 0;
        foreach (Resident resident in residents)
        {
            resident.hunger = Mathf.Min(3, resident.hunger + 1);
            if (resident.hunger >= 3) hungry++;
        }

        int unsheltered = Mathf.Max(0, residents.Count - beds);
        int penalty = hungry * 15 + unsheltered * 8;
        morale = Mathf.Max(0, morale - penalty);
        day++;
        dayClock = 100f;
        foreach (ResourcePickup resource in resources) resource.Regrow();

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
            if (morale >= 50) AddResident();
            message = "Dia " + day + ": " + hungry + " com muita fome, " + unsheltered +
                " sem cama. Perda de ânimo: " + penalty + ".";
        }
    }

    private void AddResident()
    {
        int index = residents.Count;
        residents.Add(new Resident { name = "Lume " + (index + 1), hunger = 1 });
        int column = index % 7;
        int row = index / 7;
        Vector3 position = new Vector3(-3.2f + column * 1.05f, 0.65f, 3.2f + row * 1.25f);
        GameObject resident = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        resident.name = "Lume " + (index + 1);
        resident.transform.position = position;
        resident.transform.localScale = Vector3.one * 0.8f;
        SetColor(resident, new Color(0.92f, 0.79f - (index % 3) * 0.13f, 0.40f));
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

        GUI.Box(new Rect(12, 12, 420, 162), "");
        GUI.Label(new Rect(24, 20, 395, 32), "BOSQUE VIVO   ·   DIA " + day + "/7", heading);
        GUI.Label(new Rect(24, 56, 395, 25), "Moradores: " + residents.Count + "  |  Camas: " + beds + "  |  Ânimo: " + morale, body);
        GUI.Label(new Rect(24, 82, 395, 25), "Frutas: " + fruit + "  |  Madeiras: " + wood + "  |  Anoitece em: " + Mathf.CeilToInt(dayClock) + "s", body);
        GUI.Label(new Rect(24, 111, 395, 55), message, body);

        GUI.Box(new Rect(12, Screen.height - 101, 560, 88), "");
        GUI.Label(new Rect(24, Screen.height - 92, 540, 72),
            "WASD: andar  ·  Mouse: olhar  ·  E: colher  ·  F: alimentar\n" +
            "B: construir cama (3 madeiras)  ·  N: passar a noite  ·  Esc: cursor", body);

        if (ended)
        {
            GUI.Box(new Rect(Screen.width / 2f - 240f, Screen.height / 2f - 60f, 480f, 120f), "");
            GUI.Label(new Rect(Screen.width / 2f - 220f, Screen.height / 2f - 38f, 440f, 90f), message, heading);
        }
        else if (Cursor.lockState == CursorLockMode.Locked)
        {
            GUI.Label(new Rect(Screen.width / 2f - 5f, Screen.height / 2f - 15f, 30f, 30f), "+", heading);
            ResourcePickup target = GetTarget();
            if (target != null)
            {
                GUI.Box(new Rect(Screen.width / 2f - 110f, Screen.height / 2f + 26f, 220f, 30f),
                    "E  ·  " + (target.kind == ResourcePickup.Kind.Wood ? "Coletar madeira" : "Colher frutas"));
            }
        }
    }
}
