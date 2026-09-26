using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class FirstPersonWalker : MonoBehaviour
{
    public Camera view;
    public float walkSpeed = 5f;
    public float mouseSensitivity = 2f;

    private CharacterController controller;
    private float verticalSpeed;
    private float pitch;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            bool locked = Cursor.lockState != CursorLockMode.Locked;
            Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !locked;
        }

        if (Cursor.lockState != CursorLockMode.Locked) return;

        float yaw = Input.GetAxis("Mouse X") * mouseSensitivity;
        float mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity;
        transform.Rotate(Vector3.up * yaw);
        pitch = Mathf.Clamp(pitch - mouseY, -80f, 80f);
        if (view != null) view.transform.localEulerAngles = Vector3.right * pitch;

        float horizontal = (Input.GetKey(KeyCode.D) ? 1f : 0f) - (Input.GetKey(KeyCode.A) ? 1f : 0f);
        float forward = (Input.GetKey(KeyCode.W) ? 1f : 0f) - (Input.GetKey(KeyCode.S) ? 1f : 0f);
        Vector3 direction = (transform.right * horizontal + transform.forward * forward).normalized;

        verticalSpeed = controller.isGrounded ? -1f : verticalSpeed - 20f * Time.deltaTime;
        controller.Move((direction * walkSpeed + Vector3.up * verticalSpeed) * Time.deltaTime);
    }

    private void OnDisable()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }
}
