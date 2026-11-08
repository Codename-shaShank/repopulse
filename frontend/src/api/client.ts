export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function readError(response: Response): Promise<ApiError> {
  let detail = `Request failed with status ${response.status}`;
  let code = "HttpError";
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body?.detail) && body.detail.length > 0) {
      // FastAPI's own validation errors arrive as a list of issues.
      const first = body.detail[0];
      detail = first?.msg ?? detail;
      code = "ValidationError";
    }
    if (typeof body?.code === "string") {
      code = body.code;
    }
  } catch {
    // Keep the status-based message.
  }
  return new ApiError(detail, response.status, code);
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError(
      "Could not reach the API. Check that the backend is running.",
      0,
      "NetworkError",
    );
  }

  if (!response.ok) {
    throw await readError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function exportUrl(filename: string): string {
  return `${API_BASE_URL}/api/v1/exports/${filename}`;
}
