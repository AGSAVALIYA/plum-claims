'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import {
  CalendarIcon,
  Check,
  ChevronLeft,
  ChevronRight,
  Upload,
  FileText,
  ClipboardList,
  AlertCircle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { useAuth } from '@/contexts/AuthContext';
import { submitClaimWithFiles, getClaimCategories } from '@/lib/api';
import { CLAIM_CATEGORIES, type ClaimCategoryInfo, type DocumentType } from '@/types';
import type { UploadedFileEntry } from '@/types';
import DocumentUploader from '@/components/claims/DocumentUploader';
import ClaimSubmissionAnimation from '@/components/claims/ClaimSubmissionAnimation';

// ── Validation Schema ────────────────────────────────────────

const claimFormSchema = z.object({
  claimCategory: z.string().min(1, 'Please select a claim category'),
  treatmentDate: z.date({ message: 'Please select a treatment date' }),
  claimedAmount: z
    .string()
    .min(1, 'Amount is required')
    .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
      message: 'Amount must be a positive number',
    }),
  hospitalName: z.string().optional(),
});

type ClaimFormData = z.infer<typeof claimFormSchema>;

// ── Step Config ──────────────────────────────────────────────

const STEPS = [
  { id: 1, label: 'Claim Details', icon: ClipboardList },
  { id: 2, label: 'Upload Documents', icon: Upload },
  { id: 3, label: 'Review & Submit', icon: FileText },
];

// ── Wizard Page ──────────────────────────────────────────────

export default function NewClaimPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();

  const [currentStep, setCurrentStep] = useState(1);
  const [direction, setDirection] = useState(0); // 1 = forward, -1 = backward
  const [files, setFiles] = useState<UploadedFileEntry[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [submittedClaimId, setSubmittedClaimId] = useState<number | null>(null);
  const [categories, setCategories] = useState<ClaimCategoryInfo[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    trigger,
    formState: { errors },
  } = useForm<ClaimFormData>({
    resolver: zodResolver(claimFormSchema),
    defaultValues: {
      claimCategory: '',
      claimedAmount: '',
      hospitalName: '',
    },
  });

  const watchedCategory = watch('claimCategory');
  const watchedDate = watch('treatmentDate');
  const watchedAmount = watch('claimedAmount');
  const watchedHospital = watch('hospitalName');

  // Auth guard
  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) {
      router.push('/login');
    }
  }, [user, isAuthLoading, router]);

  // Fetch policy-covered categories
  useEffect(() => {
    let cancelled = false;
    getClaimCategories()
      .then((cats) => {
        if (!cancelled) setCategories(cats);
      })
      .catch(() => {
        // Fallback to static list if API fails
        if (!cancelled) setCategories(CLAIM_CATEGORIES.map((c) => ({
          ...c,
          sub_limit: 0,
          copay_percent: 0,
          requires_prescription: false,
          requires_pre_auth: false,
        })));
      })
      .finally(() => {
        if (!cancelled) setCategoriesLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const handleCategoryChange = useCallback(
    (value: string | null) => {
      if (value !== null) {
        setValue('claimCategory', value, { shouldValidate: true });
      }
    },
    [setValue]
  );

  const handleDateChange = useCallback(
    (date: Date | undefined) => {
      if (date) {
        setValue('treatmentDate', date, { shouldValidate: true });
      }
    },
    [setValue]
  );

  const goToStep = useCallback(
    async (step: number) => {
      // Validate current step before proceeding
      if (step > currentStep) {
        let isValid = false;
        if (currentStep === 1) {
          isValid = await trigger([
            'claimCategory',
            'treatmentDate',
            'claimedAmount',
          ]);
        } else if (currentStep === 2) {
          isValid = files.length > 0;
          if (!isValid) {
            setSubmitError('Please upload at least one document');
            return;
          }
          setSubmitError(null);
          isValid = true;
        }

        if (!isValid) return;
      }

      setDirection(step > currentStep ? 1 : -1);
      setCurrentStep(step);
      setSubmitError(null);
    },
    [currentStep, trigger, files]
  );

  const handleNext = useCallback(() => {
    goToStep(currentStep + 1);
  }, [currentStep, goToStep]);

  const handleBack = useCallback(() => {
    setDirection(-1);
    setCurrentStep((prev) => Math.max(1, prev - 1));
    setSubmitError(null);
  }, []);

  // ── Submit Handler ──────────────────────────────────────────

  const onSubmit = useCallback(
    async (data: ClaimFormData) => {
      if (files.length === 0) {
        setSubmitError('Please upload at least one document');
        return;
      }

      try {
        setIsSubmitting(true);
        setSubmitError(null);

        const formData = new FormData();
        formData.append('member_id', user?.member_id ?? '');
        formData.append('claim_category', data.claimCategory);
        formData.append(
          'treatment_date',
          data.treatmentDate.toISOString().split('T')[0]
        );
        formData.append('claimed_amount', data.claimedAmount);

        if (data.hospitalName) {
          formData.append('hospital_name', data.hospitalName);
        }

        // Append files with their document types
        files.forEach((entry, index) => {
          formData.append(`documents`, entry.file);
          formData.append(`document_types`, entry.document_type);
        });

        const response = await submitClaimWithFiles(formData);
        setSubmittedClaimId(response.claim_id);
        setShowSuccess(true);
      } catch (err) {
        setSubmitError(
          err instanceof Error ? err.message : 'Failed to submit claim'
        );
      } finally {
        setIsSubmitting(false);
      }
    },
    [files, user]
  );

  // ── Step Content ──────────────────────────────────────────

  function renderStepContent() {
    switch (currentStep) {
      case 1:
        return (
          <motion.div
            key="step1"
            className="flex flex-col gap-6"
            initial={{ opacity: 0, x: direction * 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -20 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            {/* Member ID (read-only) */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="memberId">Member ID</Label>
              <Input
                id="memberId"
                value={user?.member_id ?? ''}
                readOnly
                disabled
                className="bg-muted/50 text-muted-foreground"
              />
            </div>

            {/* Claim Category */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="claimCategory">
                Claim Category <span className="text-destructive">*</span>
              </Label>
              <Select
                value={watchedCategory}
                onValueChange={handleCategoryChange}
              >
                <SelectTrigger
                  id="claimCategory"
                  className={cn(errors.claimCategory && 'border-destructive')}
                >
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent side="bottom" collisionAvoidance={{ side: 'shift' }}>
                  {categoriesLoading ? (
                    <SelectItem value="loading" disabled>Loading categories...</SelectItem>
                  ) : (
                    categories.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        <span className="mr-2">{cat.icon}</span>
                        {cat.label}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {errors.claimCategory && (
                <p className="text-xs text-destructive">
                  {errors.claimCategory.message}
                </p>
              )}
            </div>

            {/* Treatment Date */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="treatmentDate">
                Treatment Date <span className="text-destructive">*</span>
              </Label>
              <Popover>
                <PopoverTrigger
                  render={
                    <Button
                      id="treatmentDate"
                      variant="outline"
                      className={cn(
                        'h-8 w-full justify-start text-left font-normal',
                        !watchedDate && 'text-muted-foreground',
                        errors.treatmentDate && 'border-destructive'
                      )}
                    />
                  }
                >
                  <CalendarIcon className="mr-2 size-4" />
                  {watchedDate ? (
                    format(watchedDate, 'PPP')
                  ) : (
                    <span>Pick a date</span>
                  )}
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start" side="bottom" collisionAvoidance={{ side: 'shift' }}>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  <Calendar {...{
                    mode: 'single' as any,
                    selected: watchedDate,
                    onSelect: (date: Date | undefined) => handleDateChange(date),
                    disabled: (date: Date) =>
                      date > new Date() || date < new Date('1900-01-01'),
                    initialFocus: true,
                  }} />
                </PopoverContent>
              </Popover>
              {errors.treatmentDate && (
                <p className="text-xs text-destructive">
                  {errors.treatmentDate.message}
                </p>
              )}
            </div>

            {/* Claimed Amount */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="claimedAmount">
                Claimed Amount (Rs.){' '}
                <span className="text-destructive">*</span>
              </Label>
              <Input
                id="claimedAmount"
                type="number"
                min="1"
                step="0.01"
                placeholder="e.g. 5000"
                className={cn(errors.claimedAmount && 'border-destructive')}
                {...register('claimedAmount')}
              />
              {errors.claimedAmount && (
                <p className="text-xs text-destructive">
                  {errors.claimedAmount.message}
                </p>
              )}
            </div>

            {/* Hospital Name */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="hospitalName">Hospital Name</Label>
              <Input
                id="hospitalName"
                placeholder="e.g. Apollo Hospitals"
                {...register('hospitalName')}
              />
            </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            key="step2"
            className="flex flex-col gap-4"
            initial={{ opacity: 0, x: direction * 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -20 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            <div className="mb-1">
              <h3 className="text-sm font-medium text-foreground">
                Upload Supporting Documents
              </h3>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Upload at least one document to support your claim. Accepted
                formats: PDF, JPG, PNG (max 10 MB each).
              </p>
            </div>

            <DocumentUploader
              files={files}
              onFilesChange={setFiles}
              error={
                submitError?.includes('document')
                  ? submitError
                  : undefined
              }
              maxFiles={10}
            />
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            key="step3"
            className="flex flex-col gap-6"
            initial={{ opacity: 0, x: direction * 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -20 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            {/* Claim Details Summary */}
            <div>
              <h3 className="mb-3 text-sm font-medium text-foreground">
                Claim Details
              </h3>
              <Card size="sm">
                <CardContent className="grid grid-cols-2 gap-y-3 gap-x-4">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-muted-foreground">
                      Member ID
                    </span>
                    <span className="text-sm font-medium">
                      {user?.member_id}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-muted-foreground">
                      Category
                    </span>
                    <span className="text-sm font-medium">
                      {categories.find(
                        (c) => c.value === watchedCategory
                      )?.label ?? watchedCategory}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-muted-foreground">
                      Treatment Date
                    </span>
                    <span className="text-sm font-medium">
                      {watchedDate
                        ? format(watchedDate, 'PPP')
                        : 'Not set'}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-muted-foreground">
                      Claimed Amount
                    </span>
                    <span className="text-sm font-medium">
                      Rs. {watchedAmount || '0'}
                    </span>
                  </div>
                  {watchedHospital && (
                    <div className="flex flex-col gap-0.5">
                      <span className="text-xs text-muted-foreground">
                        Hospital
                      </span>
                      <span className="text-sm font-medium">
                        {watchedHospital}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <Separator />

            {/* Documents Summary */}
            <div>
              <h3 className="mb-3 text-sm font-medium text-foreground">
                Uploaded Documents ({files.length})
              </h3>
              <div className="flex flex-col gap-2">
                {files.map((entry, index) => (
                  <div
                    key={`${entry.file.name}-${index}`}
                    className="flex items-center gap-3 rounded-lg border border-border bg-card p-3"
                  >
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-muted">
                      <FileText className="size-4 text-muted-foreground" />
                    </div>
                    <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                      <span className="truncate text-sm font-medium">
                        {entry.file.name}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {(entry.file.size / 1024 / 1024).toFixed(1)} MB
                        {' — '}
                        {entry.document_type
                          ?.replace(/_/g, ' ')
                          .toLowerCase()
                          .replace(/\b\w/g, (c) => c.toUpperCase())}
                      </span>
                    </div>
                    <Check className="size-4 text-[#2D8B6E]" />
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Submit confirmation */}
            <div className="rounded-lg bg-[#E8A838]/5 border border-[#E8A838]/20 p-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 size-4 shrink-0 text-[#E8A838]" />
                <p className="text-xs text-muted-foreground">
                  By submitting this claim, you confirm that all information
                  provided is accurate and the uploaded documents are genuine.
                  False claims may result in rejection or policy cancellation.
                </p>
              </div>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  }

  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <div className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <>
      <div className="mx-auto max-w-2xl">
        <div className="flex flex-col gap-6">
          {/* Page Title */}
          <motion.h1
            className="text-2xl font-semibold tracking-tight md:text-3xl"
            style={{ fontFamily: 'var(--font-display)' }}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            Submit New Claim
          </motion.h1>

          {/* Step Indicators */}
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => {
              const StepIcon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              const isUpcoming = currentStep < step.id;

              return (
                <div
                  key={step.id}
                  className="flex flex-1 items-center"
                >
                  {/* Step circle + label */}
                  <div className="flex flex-col items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => isCompleted && goToStep(step.id)}
                      disabled={!isCompleted}
                      className={cn(
                        'flex size-8 items-center justify-center rounded-full border-2 text-xs font-medium transition-all',
                        isActive &&
                          'border-primary bg-primary text-primary-foreground',
                        isCompleted &&
                          'border-[#2D8B6E] bg-[#2D8B6E] text-white cursor-pointer',
                        isUpcoming &&
                          'border-border bg-card text-muted-foreground'
                      )}
                    >
                      {isCompleted ? (
                        <Check className="size-4" />
                      ) : (
                        <StepIcon className="size-4" />
                      )}
                    </button>
                    <span
                      className={cn(
                        'text-[11px] whitespace-nowrap',
                        isActive
                          ? 'font-medium text-foreground'
                          : isCompleted
                          ? 'text-[#2D8B6E]'
                          : 'text-muted-foreground'
                      )}
                    >
                      {step.label}
                    </span>
                  </div>

                  {/* Connector line */}
                  {index < STEPS.length - 1 && (
                    <div
                      className={cn(
                        'mx-2 mt-[-20px] h-px flex-1',
                        currentStep > step.id
                          ? 'bg-[#2D8B6E]'
                          : 'bg-border'
                      )}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Form Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Step {currentStep}: {STEPS[currentStep - 1]?.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} onKeyDown={(e) => { if (e.key === 'Enter' && currentStep !== 3) e.preventDefault(); }}>
                <AnimatePresence mode="wait">
                  {renderStepContent()}
                </AnimatePresence>

                {/* Submit error */}
                {submitError && currentStep === 3 && (
                  <motion.div
                    className="mt-4 flex items-start gap-2 rounded-md bg-destructive/5 p-3 text-sm text-destructive"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <AlertCircle className="mt-0.5 size-4 shrink-0" />
                    <span>{submitError}</span>
                  </motion.div>
                )}

                {/* Navigation Buttons */}
                <div className="mt-6 flex items-center justify-between border-t border-border pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={currentStep === 1 ? () => router.push('/claims') : handleBack}
                    className="gap-1.5"
                  >
                    <ChevronLeft className="size-4" />
                    {currentStep === 1 ? 'Cancel' : 'Back'}
                  </Button>

                  {currentStep < 3 ? (
                    <Button
                      type="button"
                      variant="default"
                      onClick={handleNext}
                      className="gap-1.5"
                    >
                      Next
                      <ChevronRight className="size-4" />
                    </Button>
                  ) : (
                    <Button
                      type="submit"
                      variant="default"
                      disabled={isSubmitting}
                      className="gap-1.5 min-w-[120px]"
                    >
                      {isSubmitting ? (
                        <>
                          <span className="size-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          Submitting...
                        </>
                      ) : (
                        <>
                          <Check className="size-4" />
                          Submit Claim
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Success Animation */}
      <ClaimSubmissionAnimation
        claimId={submittedClaimId ?? 0}
        isOpen={showSuccess}
        onClose={() => setShowSuccess(false)}
      />
    </>
  );
}
