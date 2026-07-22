import { CommandBar } from "@/components/CommandBar";
import { UserMenu } from "@/components/UserMenu";

export function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-[58px] items-center justify-between gap-3 border-b border-border bg-background/90 px-4 backdrop-blur md:px-6">
      <CommandBar />
      <div className="flex items-center gap-3">
        <UserMenu />
      </div>
    </header>
  );
}
