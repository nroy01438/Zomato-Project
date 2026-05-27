// Simplified dropdown menu component
// In production, install @radix-ui/react-dropdown-menu

import * as React from "react";

export const DropdownMenu = ({ children }: { children: React.ReactNode }) => (
  <div className="relative">{children}</div>
);

export const DropdownMenuTrigger = ({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) => (
  <div>{children}</div>
);

export const DropdownMenuContent = ({
  children,
  align = "center",
  className,
  forceMount: _forceMount,
}: {
  children: React.ReactNode;
  align?: string;
  className?: string;
  /** Accepted for Radix API compatibility; ignored in this simplified menu. */
  forceMount?: boolean;
}) => (
  <div className={`absolute z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md ${className}`}>
    {children}
  </div>
);

export const DropdownMenuItem = ({ 
  children, 
  className,
  onClick,
  asChild
}: { 
  children: React.ReactNode; 
  className?: string;
  onClick?: () => void;
  asChild?: boolean;
}) => (
  <div 
    className={`relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground ${className}`}
    onClick={onClick}
  >
    {children}
  </div>
);

export const DropdownMenuSeparator = ({ className }: { className?: string }) => (
  <div className={`-mx-1 my-1 h-px bg-muted ${className}`} />
);
