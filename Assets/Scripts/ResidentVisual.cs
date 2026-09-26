using UnityEngine;

public class ResidentVisual : MonoBehaviour
{
    public float phase;
    private Vector3 home;

    private void Start()
    {
        home = transform.position;
    }

    private void Update()
    {
        transform.position = home + Vector3.up * (0.08f * Mathf.Sin(Time.time * 2f + phase));
    }
}
