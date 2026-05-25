export class AppError extends Error {
  constructor(message, { status = 500, code = "APP_ERROR", cause } = {}) {
    super(message);
    this.name = "AppError";
    this.status = status;
    this.code = code;
    if (cause) this.cause = cause;
  }
}

export function toPublicError(err) {
  if (err instanceof AppError) {
    return { status: err.status, code: err.code, message: err.message };
  }
  return { status: 500, code: "INTERNAL_ERROR", message: "Internal server error" };
}

