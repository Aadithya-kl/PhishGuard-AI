import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl py-10">
      <h1 className="t-h1">This page doesn’t exist</h1>
      <p className="mt-2 text-mute">The link may be old, or the item was deleted.</p>
      <Link href="/" className="mt-6 inline-block text-ice hover:underline">Back to overview</Link>
    </div>
  );
}
