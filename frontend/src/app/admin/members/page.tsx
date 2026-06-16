'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Search, Users, AlertCircle, RefreshCw, FileText } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { listMembers } from '@/lib/api';

// ── Types ───────────────────────────────────────────────────

interface Member {
  member_id: string;
  member_name: string;
  role: string;
}

// ── Animation Variants ──────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] as const } },
};

// ── Loading Skeleton ─────────────────────────────────────────

function MembersSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      <div className="h-8 w-48 bg-muted rounded-lg" />
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="h-4 w-40 bg-muted rounded" />
        </div>
        <div className="divide-y divide-border">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-4">
              <div className="h-4 w-24 bg-muted rounded" />
              <div className="h-4 w-32 bg-muted rounded" />
              <div className="h-5 w-16 bg-muted rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main Members Page ───────────────────────────────────────

export default function AdminMembersPage() {
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [filtered, setFiltered] = useState<Member[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMembers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listMembers();
      setMembers(result.members);
      setFiltered(result.members);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load members');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  // Filter when search changes
  useEffect(() => {
    if (!search.trim()) {
      setFiltered(members);
      return;
    }
    const q = search.toLowerCase();
    setFiltered(
      members.filter(
        (m) =>
          m.member_id.toLowerCase().includes(q) ||
          m.member_name.toLowerCase().includes(q)
      )
    );
  }, [search, members]);

  const handleMemberClick = useCallback(
    (memberId: string) => {
      router.push(`/admin/claims?member_id=${encodeURIComponent(memberId)}`);
    },
    [router]
  );

  // ── Loading State ──────────────────────────────────────────
  if (loading && members.length === 0) {
    return <MembersSkeleton />;
  }

  // ── Error State ────────────────────────────────────────────
  if (error && members.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-24 gap-4"
      >
        <div className="size-12 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertCircle className="size-6 text-destructive" />
        </div>
        <p className="text-muted-foreground text-sm max-w-md text-center">{error}</p>
        <Button variant="outline" onClick={fetchMembers}>
          <RefreshCw className="size-4 mr-1.5" />
          Retry
        </Button>
      </motion.div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <h1
          className="text-2xl sm:text-3xl font-bold tracking-tight"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Members
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          View members and their claims
        </p>
      </motion.div>

      {/* Search */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardContent className="pt-4">
            <div className="relative max-w-xs">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
              <Input
                placeholder="Search by member ID or name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8"
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Summary */}
      <motion.div variants={itemVariants}>
        <p className="text-sm text-muted-foreground">
          {filtered.length === members.length
            ? `${members.length.toLocaleString()} member${members.length !== 1 ? 's' : ''}`
            : `Showing ${filtered.length} of ${members.length.toLocaleString()} members`}
        </p>
      </motion.div>

      {/* Members Table */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardContent className="p-0">
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <div className="size-12 rounded-full bg-muted flex items-center justify-center">
                  <Users className="size-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground font-medium">
                  {search ? 'No members match your search' : 'No members found'}
                </p>
                {search && (
                  <Button variant="outline" size="sm" onClick={() => setSearch('')}>
                    Clear search
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Member ID</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filtered.map((member) => (
                      <TableRow
                        key={member.member_id}
                        className="cursor-pointer"
                        onClick={() => handleMemberClick(member.member_id)}
                      >
                        <TableCell className="font-mono text-xs font-medium">
                          {member.member_id}
                        </TableCell>
                        <TableCell className="text-sm font-medium">
                          {member.member_name}
                        </TableCell>
                        <TableCell>
                          {member.role === 'admin' ? (
                            <Badge
                              variant="outline"
                              className="bg-[#0D6B6E]/10 text-[#0D6B6E] border-[#0D6B6E]/20 font-medium"
                            >
                              Admin
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="bg-muted text-muted-foreground border-border font-medium"
                            >
                              Member
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMemberClick(member.member_id);
                            }}
                          >
                            <FileText className="size-4 mr-1.5" />
                            View Claims
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
