import { useState, type FormEvent } from "react";

const OWNER_PATTERN = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/;
const NAME_PATTERN = /^[A-Za-z0-9._-]{1,100}$/;

export function AddRepositoryForm({
  onAdd,
  busy,
}: {
  onAdd: (owner: string, name: string) => Promise<void>;
  busy: boolean;
}) {
  const [owner, setOwner] = useState("");
  const [name, setName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmedOwner = owner.trim();
    const trimmedName = name.trim();

    if (!OWNER_PATTERN.test(trimmedOwner)) {
      setLocalError("Enter a GitHub owner such as fastapi, not a URL.");
      return;
    }
    if (!NAME_PATTERN.test(trimmedName)) {
      setLocalError("Enter a repository name such as fastapi, not a URL.");
      return;
    }

    setLocalError(null);
    await onAdd(trimmedOwner, trimmedName);
    setOwner("");
    setName("");
  }

  return (
    <form className="add-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="owner">Owner</label>
        <input
          id="owner"
          value={owner}
          onChange={(event) => setOwner(event.target.value)}
          placeholder="fastapi"
          autoComplete="off"
          disabled={busy}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="name">Repository</label>
        <input
          id="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="fastapi"
          autoComplete="off"
          disabled={busy}
          required
        />
      </div>
      <button type="submit" className="primary" disabled={busy}>
        {busy ? "Adding…" : "Track repository"}
      </button>
      {localError ? (
        <p className="field-error" role="alert">
          {localError}
        </p>
      ) : null}
    </form>
  );
}
