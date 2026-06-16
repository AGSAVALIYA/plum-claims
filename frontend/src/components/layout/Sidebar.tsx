'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  FileText,
  PlusCircle,
  ShieldCheck,
  Users,
  ClipboardCheck,
  LogOut,
  Menu,
  ChevronLeft,
  Stethoscope,
  BookOpen,
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
  memberOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'My Claims', href: '/claims', icon: FileText, memberOnly: true },
  { label: 'New Claim', href: '/claims/new', icon: PlusCircle, memberOnly: true },
  { label: 'Admin Overview', href: '/admin', icon: ShieldCheck, adminOnly: true },
  { label: 'All Claims', href: '/admin/claims', icon: ClipboardCheck, adminOnly: true },
  { label: 'Members', href: '/admin/members', icon: Users, adminOnly: true },
  { label: 'Policy', href: '/admin/policy', icon: BookOpen, adminOnly: true },
];

function SidebarContent({ collapsed, onClose }: { collapsed?: boolean; onClose?: () => void }) {
  const pathname = usePathname();
  const { user, logout, isAdmin } = useAuth();

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.adminOnly && !isAdmin) return false;
    if (item.memberOnly && isAdmin) return false;
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-[var(--sidebar)] text-[var(--sidebar-foreground)]">
      {/* Brand */}
      <div className={cn('flex items-center gap-3 px-4 h-16 shrink-0', collapsed && 'justify-center px-2')}>
        <div className="w-9 h-9 rounded-lg bg-[var(--sidebar-primary)] flex items-center justify-center shrink-0">
          <Stethoscope className="w-5 h-5 text-[var(--sidebar-primary-foreground)]" />
        </div>
        {!collapsed && (
          <span className="font-display text-lg font-bold tracking-tight">ClaimFlow</span>
        )}
      </div>

      <Separator className="bg-[var(--sidebar-border)]" />

      {/* Navigation */}
      <ScrollArea className="flex-1 py-3">
        <nav className={cn('flex flex-col gap-0.5', collapsed ? 'px-2' : 'px-3')}>
          {visibleItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 rounded-lg text-sm font-medium transition-all duration-150',
                  collapsed ? 'justify-center px-0 py-2' : 'px-3 py-2.5',
                  isActive
                    ? 'bg-[var(--sidebar-accent)] text-[var(--sidebar-accent-foreground)]'
                    : 'text-[var(--sidebar-foreground)]/70 hover:text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)]/50'
                )}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </ScrollArea>

      {/* User + Logout */}
      <div className={cn('p-3 border-t border-[var(--sidebar-border)]', collapsed && 'px-2')}>
        {user && !collapsed && (
          <div className="mb-2 px-3">
            <p className="text-xs font-medium text-[var(--sidebar-foreground)]/60">Signed in as</p>
            <p className="text-sm font-semibold truncate">{user.member_name}</p>
            <span className="inline-block mt-0.5 text-[10px] uppercase tracking-wider font-bold rounded-full bg-[var(--sidebar-accent)] text-[var(--sidebar-accent-foreground)] px-2 py-0.5">
              {user.role}
            </span>
          </div>
        )}
        <Button
          variant="ghost"
          onClick={logout}
          className={cn(
            'w-full text-[var(--sidebar-foreground)]/70 hover:text-red-400 hover:bg-red-500/10 justify-start gap-3',
            collapsed && 'justify-center px-0'
          )}
          title="Sign out"
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && 'Sign out'}
        </Button>
      </div>
    </div>
  );
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={cn(
          'hidden lg:flex flex-col h-screen sticky top-0 transition-all duration-300 shrink-0',
          collapsed ? 'w-[68px]' : 'w-[260px]'
        )}
      >
        <SidebarContent collapsed={collapsed} />
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="absolute -right-3 top-7 w-6 h-6 rounded-full bg-[var(--sidebar)] border border-[var(--sidebar-border)] flex items-center justify-center text-[var(--sidebar-foreground)]/50 hover:text-[var(--sidebar-foreground)] transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeft className={cn('w-3.5 h-3.5 transition-transform', collapsed && 'rotate-180')} />
        </button>
      </aside>

      {/* Mobile sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger
          render={<Button variant="ghost" size="icon" className="lg:hidden fixed top-3 left-3 z-50" />}
        >
          <Menu className="w-5 h-5" />
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-[280px] bg-[var(--sidebar)] border-r-[var(--sidebar-border)]">
          <VisuallyHidden>
            <SheetTitle>Navigation Menu</SheetTitle>
          </VisuallyHidden>
          <SidebarContent
            onClose={() => setMobileOpen(false)}
          />
        </SheetContent>
      </Sheet>
    </>
  );
}
