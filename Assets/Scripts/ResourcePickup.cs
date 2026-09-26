using UnityEngine;

public class ResourcePickup : MonoBehaviour
{
    public enum Kind { Fruit, Wood }

    public Kind kind;
    public int amount = 2;
    public bool available = true;

    public int Harvest()
    {
        if (!available) return 0;
        available = false;
        gameObject.SetActive(false);
        return amount;
    }

    public void Regrow()
    {
        available = true;
        gameObject.SetActive(true);
    }
}
