'use client';

import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { LogOut, User } from 'lucide-react';
import { cn } from '@/lib/utils';

// Path-to-title mapping
const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/claims': 'My Claims',
  '/admin': 'Admin Overview',
  '/admin/claims': 'All Claims',
  '/admin/members': 'Members',
};

function getPageTitle(pathname: string): string {
  // Direct match
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  // Match claims/new, claims/[id], admin/claims/[id]
  if (pathname.startsWith('/claims/new')) return 'Submit New Claim';
  if (pathname.startsWith('/claims/')) return 'Claim Details';
  if (pathname.startsWith('/admin/claims/')) return 'Claim Review';
  if (pathname.startsWith('/login')) return 'Sign In';
  return 'ClaimFlow';
}

export function Header() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const title = getPageTitle(pathname);

  const initials = user?.member_name
    ? user.member_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : '?';

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-6 bg-background/80 backdrop-blur-sm border-b border-border">
      <div className="flex items-center gap-3">
        {/* Mobile: spacer for Sheet trigger */}
        <div className="lg:hidden w-10" />
        <h1 className="font-display text-xl font-bold text-foreground tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        {/* Notification bell — disabled until notification system is implemented */}
        {/* <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground" aria-label="Notifications">
          <Bell className="w-5 h-5" />
        </Button> */}

        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button variant="ghost" className="flex items-center gap-2 px-2 py-1.5 rounded-full hover:bg-muted" />
            }
          >
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-primary text-primary-foreground text-xs font-bold">
                {initials}
              </AvatarFallback>
            </Avatar>
            <span className="hidden sm:inline text-sm font-medium text-foreground max-w-[120px] truncate">
              {user?.member_name || 'User'}
            </span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="px-3 py-2.5">
              <p className="text-sm font-semibold">{user?.member_name}</p>
              <p className="text-xs text-muted-foreground">{user?.member_id}</p>
              <span className="inline-block mt-1 text-[10px] uppercase tracking-wider font-bold rounded-full bg-primary/10 text-primary px-2 py-0.5">
                {user?.role}
              </span>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="flex items-center gap-2">
              <User className="w-4 h-4" /> Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={logout} className="cursor-pointer flex items-center gap-2 text-destructive">
              <LogOut className="w-4 h-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
