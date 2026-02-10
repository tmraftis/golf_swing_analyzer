export default function Footer() {
  return (
    <footer className="border-t border-cream/10 px-6 py-8">
      <div className="mx-auto max-w-6xl flex flex-col sm:flex-row items-center justify-between gap-4 text-cream/40 text-sm">
        <span>
          <span className="font-semibold tracking-wider text-cream/60">PURE</span>{" "}
          &mdash; Swing pure
        </span>
        <span>&copy; {new Date().getFullYear()} Pure. All rights reserved.</span>
      </div>
    </footer>
  );
}
