'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  ArrowLeft,
  AlertCircle,
  RefreshCw,
  User,
  CalendarDays,
  Users,
  FileText,
  DollarSign,
  ShieldCheck,
  KeyRound,
  Activity,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { getMemberDetail, resetMemberPassword, listAdminClaims } from '@/lib/api';
import type { MemberDetail, ClaimResponse } from '@/types';

// ── Animation Variants ──────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] as const } },
};

// ── Stat Card ───────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color = 'text-foreground',
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-3">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted">
        <Icon className="size-4 text-muted-foreground" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={`text-sm font-semibold ${color}`}>{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────

export default function MemberDetailPage() {
  const params = useParams();
  const router = useRouter();
  const memberId = params.id as string;

  const [member, setMember] = useState<MemberDetail | null>(null);
  const [recentClaims, setRecentClaims] = useState<ClaimResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [resetting, setResetting] = useState(false);

  const fetchMember = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMemberDetail(memberId);
      setMember(data);
      // Also fetch recent claims
      try {
        const claims = await listAdminClaims({ member_id: memberId, limit: 5 });
        setRecentClaims(claims.claims);
      } catch {
        // Non-fatal
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load member');
    } finally {
      setLoading(false);
    }
  }, [memberId]);

  useEffect(() => {
    fetchMember();
  }, [fetchMember]);

  const handleResetPassword = async () => {
    if (newPassword.length < 4) {
      toast.error('Password must be at least 4 characters');
      return;
    }
    setResetting(true);
    try {
      await resetMemberPassword(memberId, newPassword);
      toast.success(`Password reset for ${memberId}`);
      setResetDialogOpen(false);
      setNewPassword('');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setResetting(false);
    }
  };

  // ── Loading State ──────────────────────────────────────────

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 w-64 bg-muted rounded-lg" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-muted rounded-lg" />
          ))}
        </div>
        <div className="h-48 bg-muted rounded-lg" />
      </div>
    );
  }

  // ── Error State ────────────────────────────────────────────

  if (error || !member) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-24 gap-4"
      >
        <div className="size-12 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertCircle className="size-6 text-destructive" />
        </div>
        <p className="text-muted-foreground text-sm max-w-md text-center">{error || 'Member not found'}</p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push('/admin/members')}>
            <ArrowLeft className="size-4 mr-1.5" />
            Back to Members
          </Button>
          <Button variant="outline" onClick={fetchMember}>
            <RefreshCw className="size-4 mr-1.5" />
            Retry
          </Button>
        </div>
      </motion.div>
    );
  }

  const summary = member.claims_summary;

  return (
    <>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/admin/members')}
            >
              <ArrowLeft className="size-4" />
            </Button>
            <div>
              <h1
                className="text-2xl font-bold tracking-tight"
                style={{ fontFamily: 'var(--font-display)' }}
              >
                {member.name}
              </h1>
              <p className="text-sm text-muted-foreground">{member.member_id}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push(`/admin/claims?member_id=${memberId}`)}
            >
              <FileText className="size-4 mr-1.5" />
              View Claims
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setResetDialogOpen(true)}
            >
              <KeyRound className="size-4 mr-1.5" />
              Reset Password
            </Button>
          </div>
        </motion.div>

        {/* Profile Card */}
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <User className="size-4" />
                Profile
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Member ID</p>
                  <p className="text-sm font-mono font-medium">{member.member_id}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Date of Birth</p>
                  <p className="text-sm font-medium">{member.date_of_birth || '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Gender</p>
                  <p className="text-sm font-medium">{member.gender || '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Relationship</p>
                  <Badge variant="outline" className="font-medium">
                    {member.relationship || '—'}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Join Date</p>
                  <p className="text-sm font-medium">{member.join_date || '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Role</p>
                  <Badge
                    variant="outline"
                    className={
                      member.role === 'admin'
                        ? 'bg-[#0D6B6E]/10 text-[#0D6B6E] border-[#0D6B6E]/20'
                        : 'bg-muted text-muted-foreground border-border'
                    }
                  >
                    {member.role === 'admin' ? 'Admin' : 'Member'}
                  </Badge>
                </div>
                {member.primary_member_id && (
                  <div>
                    <p className="text-xs text-muted-foreground">Primary Member</p>
                    <Button
                      variant="link"
                      className="h-auto p-0 text-sm font-medium"
                      onClick={() => router.push(`/admin/members/${member.primary_member_id}`)}
                    >
                      {member.primary_member_id}
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Claims Summary */}
        {summary && (
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="size-4" />
                  Claims Summary ({summary.year})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard
                    icon={FileText}
                    label="Total Claims"
                    value={summary.total_claims_count}
                  />
                  <StatCard
                    icon={DollarSign}
                    label="Approved Amount"
                    value={`Rs. ${summary.approved_claims_amount.toLocaleString()}`}
                    sub={`${summary.approved_claims_count} approved`}
                    color="text-[#2D8B6E]"
                  />
                  <StatCard
                    icon={ShieldCheck}
                    label="Family Floater Used"
                    value={`Rs. ${summary.family_approved_amount.toLocaleString()}`}
                    sub={`Limit: Rs. ${summary.family_combined_limit.toLocaleString()}`}
                  />
                  <StatCard
                    icon={CalendarDays}
                    label="Last Claim"
                    value={summary.last_claim_date || 'None'}
                  />
                </div>

                {/* Progress bar for family floater */}
                {summary.family_combined_limit > 0 && (
                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Family Floater Usage</span>
                      <span>
                        {Math.round(
                          (summary.family_approved_amount / summary.family_combined_limit) * 100
                        )}
                        %
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#0D6B6E] rounded-full transition-all"
                        style={{
                          width: `${Math.min(
                            (summary.family_approved_amount / summary.family_combined_limit) * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Dependents */}
        {member.dependents.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="size-4" />
                  Dependents ({member.dependents.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Member ID</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Relationship</TableHead>
                      <TableHead>DOB</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {member.dependents.map((dep) => (
                      <TableRow key={dep.member_id}>
                        <TableCell className="font-mono text-xs">{dep.member_id}</TableCell>
                        <TableCell className="text-sm font-medium">{dep.name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{dep.relationship}</Badge>
                        </TableCell>
                        <TableCell className="text-sm">{dep.date_of_birth || '—'}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => router.push(`/admin/members/${dep.member_id}`)}
                          >
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Recent Claims */}
        {recentClaims.length > 0 && (
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="size-4" />
                  Recent Claims
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Claim ID</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Decision</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentClaims.map((claim) => (
                      <TableRow key={claim.claim_id}>
                        <TableCell className="font-mono text-xs">#{claim.claim_id}</TableCell>
                        <TableCell className="text-sm">{claim.claim_category}</TableCell>
                        <TableCell className="text-sm">{claim.treatment_date || '—'}</TableCell>
                        <TableCell className="text-sm">Rs. {claim.claimed_amount?.toLocaleString() || '—'}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">
                            {claim.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {claim.decision ? (
                            <Badge
                              variant="outline"
                              className={
                                claim.decision === 'APPROVED'
                                  ? 'bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20'
                                  : claim.decision === 'REJECTED'
                                  ? 'bg-destructive/10 text-destructive border-destructive/20'
                                  : 'bg-[#E8A838]/10 text-[#E8A838] border-[#E8A838]/20'
                              }
                            >
                              {claim.decision}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => router.push(`/admin/claims/${claim.claim_id}`)}
                          >
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </motion.div>

      {/* Reset Password Dialog */}
      <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password</DialogTitle>
            <DialogDescription>
              Set a new password for <strong>{member.name}</strong> ({member.member_id}).
              The member will use this password to log in.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm font-medium" htmlFor="new-password">
              New Password
            </label>
            <Input
              id="new-password"
              type="password"
              placeholder="Min 4 characters"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="mt-1.5"
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleResetPassword();
              }}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setResetDialogOpen(false);
                setNewPassword('');
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={resetting || newPassword.length < 4}
            >
              {resetting ? 'Resetting...' : 'Reset Password'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
