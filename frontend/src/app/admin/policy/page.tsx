'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  RefreshCw,
  ShieldCheck,
  Building,
  Clock,
  Ban,
  FileCheck,
  AlertTriangle,
  DollarSign,
  Stethoscope,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { getPolicy } from '@/lib/api';

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

// ── Helpers ─────────────────────────────────────────────────

function formatCurrency(value: unknown): string {
  const num = Number(value);
  if (isNaN(num)) return String(value);
  return `Rs. ${num.toLocaleString()}`;
}

// ── Main Page ───────────────────────────────────────────────

export default function AdminPolicyPage() {
  const [policy, setPolicy] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPolicy = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPolicy();
      setPolicy(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load policy');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPolicy();
  }, [fetchPolicy]);

  // ── Loading State ──────────────────────────────────────────

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 w-48 bg-muted rounded-lg" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-40 bg-muted rounded-lg" />
        ))}
      </div>
    );
  }

  // ── Error State ────────────────────────────────────────────

  if (error || !policy) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-24 gap-4"
      >
        <div className="size-12 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertCircle className="size-6 text-destructive" />
        </div>
        <p className="text-muted-foreground text-sm max-w-md text-center">{error || 'Policy not found'}</p>
        <Button variant="outline" onClick={fetchPolicy}>
          <RefreshCw className="size-4 mr-1.5" />
          Retry
        </Button>
      </motion.div>
    );
  }

  // Extract policy sections
  const policyId = policy.policy_id as string || 'Unknown';
  const policyName = policy.policy_name as string || '';
  const insurer = policy.insurer as string || '';
  const policyHolder = (policy.policy_holder || {}) as Record<string, unknown>;
  const coverage = (policy.coverage || {}) as Record<string, unknown>;
  const opdCategories = (policy.opd_categories || {}) as Record<string, Record<string, unknown>>;
  const waitingPeriods = (policy.waiting_periods || {}) as Record<string, unknown>;
  const specificWaitingPeriods = (waitingPeriods.specific_conditions || {}) as Record<string, number>;
  const exclusions = (policy.exclusions || {}) as Record<string, unknown>;
  const preAuth = (policy.pre_authorization || {}) as Record<string, unknown>;
  const networkHospitals = (policy.network_hospitals || []) as string[];
  const documentReqs = (policy.document_requirements || {}) as Record<string, Record<string, unknown>>;
  const submissionRules = (policy.submission_rules || {}) as Record<string, unknown>;
  const fraudThresholds = (policy.fraud_thresholds || {}) as Record<string, unknown>;
  const familyFloater = (coverage.family_floater || {}) as Record<string, unknown>;

  const CATEGORY_LABELS: Record<string, { label: string; icon: string }> = {
    consultation: { label: 'Consultation', icon: '🩺' },
    diagnostic: { label: 'Diagnostic', icon: '🔬' },
    pharmacy: { label: 'Pharmacy', icon: '💊' },
    dental: { label: 'Dental', icon: '🦷' },
    vision: { label: 'Vision', icon: '👁️' },
    alternative_medicine: { label: 'Alternative Medicine', icon: '🌿' },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1
          className="text-2xl sm:text-3xl font-bold tracking-tight"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Policy Configuration
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {policyName} — {insurer}
        </p>
      </motion.div>

      {/* Policy Overview */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <ShieldCheck className="size-4" />
              Policy Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Policy ID</p>
                <p className="text-sm font-mono font-medium">{policyId}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Insurer</p>
                <p className="text-sm font-medium">{insurer}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Company</p>
                <p className="text-sm font-medium">{String(policyHolder.company_name || '—')}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Employees</p>
                <p className="text-sm font-medium">{String(policyHolder.employee_count || '—')}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Start Date</p>
                <p className="text-sm font-medium">{String(policyHolder.policy_start_date || '—')}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">End Date</p>
                <p className="text-sm font-medium">{String(policyHolder.policy_end_date || '—')}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Status</p>
                <Badge variant="outline" className="bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20">
                  {String(policyHolder.renewal_status || '—')}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Coverage Limits */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <DollarSign className="size-4" />
              Coverage Limits
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs text-muted-foreground">Sum Insured / Employee</p>
                <p className="text-lg font-semibold text-status-info">{formatCurrency(coverage.sum_insured_per_employee)}</p>
              </div>
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs text-muted-foreground">Annual OPD Limit</p>
                <p className="text-lg font-semibold">{formatCurrency(coverage.annual_opd_limit)}</p>
              </div>
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs text-muted-foreground">Per-Claim Limit</p>
                <p className="text-lg font-semibold">{formatCurrency(coverage.per_claim_limit)}</p>
              </div>
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs text-muted-foreground">Family Floater</p>
                <p className="text-lg font-semibold">
                  {(familyFloater.enabled as boolean) ? formatCurrency(familyFloater.combined_limit) : 'Disabled'}
                </p>
                {(familyFloater.enabled as boolean) && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Covers: {(familyFloater.covered_relationships as string[] || []).join(', ')}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* OPD Categories */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Stethoscope className="size-4" />
              Claim Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead>Sub-Limit</TableHead>
                  <TableHead>Co-pay</TableHead>
                  <TableHead>Network Discount</TableHead>
                  <TableHead>Requires Prescription</TableHead>
                  <TableHead>Pre-Auth</TableHead>
                  <TableHead>Covered</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(opdCategories).map(([key, config]) => {
                  const meta = CATEGORY_LABELS[key] || { label: key, icon: '📋' };
                  return (
                    <TableRow key={key}>
                      <TableCell className="font-medium">
                        <span className="mr-2">{meta.icon}</span>
                        {meta.label}
                      </TableCell>
                      <TableCell>{formatCurrency(config.sub_limit)}</TableCell>
                      <TableCell>{String(config.copay_percent || 0)}%</TableCell>
                      <TableCell>{String(config.network_discount_percent || 0)}%</TableCell>
                      <TableCell>
                        {config.requires_prescription ? (
                          <Badge variant="outline" className="bg-status-info/10 text-status-info border-status-info/20 text-xs">
                            Yes
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground">No</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {config.requires_pre_auth ? (
                          <Badge variant="outline" className="bg-[#E8A838]/10 text-[#E8A838] border-[#E8A838]/20 text-xs">
                            Required
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground">No</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {config.covered ? (
                          <Badge variant="outline" className="bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20 text-xs">
                            Covered
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 text-xs">
                            Not Covered
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </motion.div>

      {/* Waiting Periods */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="size-4" />
              Waiting Periods
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs text-muted-foreground">Initial Waiting Period</p>
                <p className="text-lg font-semibold">{String(waitingPeriods.initial_waiting_period_days || 0)} days</p>
              </div>
              <div className="rounded-lg border border-border bg-card p-3">
                <p className="text-xs text-muted-foreground">Pre-existing Conditions</p>
                <p className="text-lg font-semibold">{String(waitingPeriods.pre_existing_conditions_days || 0)} days</p>
              </div>
            </div>
            {Object.keys(specificWaitingPeriods).length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Condition</TableHead>
                    <TableHead>Waiting Period</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(specificWaitingPeriods).map(([condition, days]) => (
                    <TableRow key={condition}>
                      <TableCell className="font-medium capitalize">
                        {condition.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell>{days} days</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Exclusions */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Ban className="size-4" />
              Exclusions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* General Exclusions */}
            <div>
              <p className="text-sm font-medium mb-2">Excluded Conditions</p>
              <div className="flex flex-wrap gap-2">
                {((exclusions.conditions || []) as string[]).map((cond) => (
                  <Badge key={cond} variant="outline" className="bg-destructive/5 text-destructive border-destructive/20">
                    {cond}
                  </Badge>
                ))}
              </div>
            </div>
            <Separator />
            {/* Dental Exclusions */}
            <div>
              <p className="text-sm font-medium mb-2">Dental Exclusions</p>
              <div className="flex flex-wrap gap-2">
                {((exclusions.dental_exclusions || []) as string[]).map((exc) => (
                  <Badge key={exc} variant="outline" className="bg-[#E8A838]/5 text-[#E8A838] border-[#E8A838]/20">
                    {exc}
                  </Badge>
                ))}
              </div>
            </div>
            <Separator />
            {/* Vision Exclusions */}
            <div>
              <p className="text-sm font-medium mb-2">Vision Exclusions</p>
              <div className="flex flex-wrap gap-2">
                {((exclusions.vision_exclusions || []) as string[]).map((exc) => (
                  <Badge key={exc} variant="outline" className="bg-[#E8A838]/5 text-[#E8A838] border-[#E8A838]/20">
                    {exc}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Pre-Authorization */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileCheck className="size-4" />
              Pre-Authorization Requirements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {((preAuth.required_for || []) as string[]).map((req) => (
                <div key={req} className="flex items-center gap-2 text-sm">
                  <AlertTriangle className="size-3.5 text-[#E8A838] shrink-0" />
                  {req}
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              Pre-authorization validity: {String(preAuth.validity_days || 30)} days
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Network Hospitals */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Building className="size-4" />
              Network Hospitals ({networkHospitals.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {networkHospitals.map((hospital) => (
                <div key={hospital} className="flex items-center gap-2 text-sm rounded-md border border-border px-3 py-2">
                  <Building className="size-3.5 text-muted-foreground shrink-0" />
                  {hospital}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Document Requirements */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileCheck className="size-4" />
              Document Requirements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead>Required Documents</TableHead>
                  <TableHead>Optional Documents</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(documentReqs).map(([category, reqs]) => {
                  const meta = CATEGORY_LABELS[category.toLowerCase()] || { label: category, icon: '📋' };
                  return (
                    <TableRow key={category}>
                      <TableCell className="font-medium">
                        <span className="mr-2">{meta.icon}</span>
                        {meta.label}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {((reqs.required || []) as string[]).map((doc) => (
                            <Badge key={doc} variant="outline" className="text-xs">
                              {doc.replace(/_/g, ' ')}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {((reqs.optional || []) as string[]).length > 0
                            ? ((reqs.optional || []) as string[]).map((doc) => (
                                <Badge key={doc} variant="outline" className="text-xs text-muted-foreground">
                                  {doc.replace(/_/g, ' ')}
                                </Badge>
                              ))
                            : <span className="text-xs text-muted-foreground">—</span>}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </motion.div>

      {/* Submission Rules & Fraud Thresholds */}
      <motion.div variants={itemVariants}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Submission Rules</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Deadline from treatment</span>
                <span className="font-medium">{String(submissionRules.deadline_days_from_treatment || 30)} days</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Minimum claim amount</span>
                <span className="font-medium">{formatCurrency(submissionRules.minimum_claim_amount)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Currency</span>
                <span className="font-medium">{String(submissionRules.currency || 'INR')}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <AlertTriangle className="size-4" />
                Fraud Thresholds
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Same-day claims limit</span>
                <span className="font-medium">{String(fraudThresholds.same_day_claims_limit || 2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Monthly claims limit</span>
                <span className="font-medium">{String(fraudThresholds.monthly_claims_limit || 6)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">High-value threshold</span>
                <span className="font-medium">{formatCurrency(fraudThresholds.high_value_claim_threshold)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Auto manual-review above</span>
                <span className="font-medium">{formatCurrency(fraudThresholds.auto_manual_review_above)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Fraud score threshold</span>
                <span className="font-medium">{String(fraudThresholds.fraud_score_manual_review_threshold || 0.8)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </motion.div>
  );
}
