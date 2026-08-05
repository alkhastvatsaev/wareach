"use client";

type Props = { telegramUrl: string };

export function TelegramSticky({ telegramUrl }: Props) {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-white/10 bg-[#060b10]/95 p-3 backdrop-blur-md md:hidden">
      <a
        href={telegramUrl}
        target="_blank"
        rel="noreferrer"
        className="flex min-h-11 w-full items-center justify-center rounded-xl bg-[var(--accent)] text-sm font-semibold text-white"
      >
        Contacter sur Telegram
      </a>
    </div>
  );
}
