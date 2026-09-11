let csrf = "";
async function request<T>(
  path: string,
  method: string,
  body?: unknown,
  retryCsrf = true,
): Promise<T> {
  const response = await fetch(`/api/v1/${path}`, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response
    .json()
    .catch(() => ({ detail: "The server did not return a valid response." }));
  if (data.csrf) csrf = data.csrf;
  if (
    retryCsrf &&
    method !== "GET" &&
    response.status === 403 &&
    data.detail === "CSRF validation failed."
  ) {
    const refresh = await fetch("/api/v1/session/", {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
    });
    const session = await refresh.json().catch(() => ({}));
    if (refresh.ok && session.csrf) {
      csrf = session.csrf;
      return request<T>(path, method, body, false);
    }
  }
  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : Object.entries(data)
            .map(
              ([key, value]) =>
                `${key.replaceAll("_", " ")}: ${Array.isArray(value) ? value.join(" ") : value}`,
            )
            .join(" · ");
    throw new Error(detail || "Something went wrong. Please try again.");
  }
  return data as T;
}

export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  return request<T>(path, method, body);
}
