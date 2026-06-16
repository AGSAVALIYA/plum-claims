'use client';

import { useRef, useCallback, useState } from 'react';
import { Upload, X, FileText, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DOCUMENT_TYPE_LABELS, type DocumentType, DOCUMENT_TYPES } from '@/types';

export interface UploadedFileEntry {
  file: File;
  document_type: DocumentType;
}

interface DocumentUploaderProps {
  files: UploadedFileEntry[];
  onFilesChange: (files: UploadedFileEntry[]) => void;
  error?: string;
  maxFiles?: number;
}

const ALLOWED_TYPES = ['.pdf', '.jpg', '.jpeg', '.png'];
const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() ?? '';
}

export default function DocumentUploader({
  files,
  onFilesChange,
  error,
  maxFiles = 10,
}: DocumentUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      const ext = getFileExtension(file.name);
      if (!ALLOWED_TYPES.includes(`.${ext}`)) {
        return `"${file.name}" has an unsupported file type. Allowed: .pdf, .jpg, .png`;
      }
      if (!ALLOWED_MIME_TYPES.includes(file.type)) {
        return `"${file.name}" has an unsupported file type. Allowed: .pdf, .jpg, .png`;
      }
      if (file.size > MAX_FILE_SIZE) {
        return `"${file.name}" exceeds the 10 MB size limit (${formatFileSize(file.size)})`;
      }
      return null;
    },
    []
  );

  const addFiles = useCallback(
    (newFileList: FileList | File[]) => {
      setLocalError(null);
      const newEntries: UploadedFileEntry[] = [];
      const fileArray = Array.from(newFileList);

      if (files.length + fileArray.length > maxFiles) {
        setLocalError(`You can upload a maximum of ${maxFiles} files.`);
        return;
      }

      const existingNames = new Set(files.map((f) => f.file.name));

      for (const file of fileArray) {
        if (existingNames.has(file.name)) {
          setLocalError(`"${file.name}" has already been added.`);
          continue;
        }

        const validationError = validateFile(file);
        if (validationError) {
          setLocalError(validationError);
          continue;
        }

        newEntries.push({
          file,
          document_type: 'PRESCRIPTION' as DocumentType,
        });
      }

      if (newEntries.length > 0) {
        onFilesChange([...files, ...newEntries]);
      }
    },
    [files, maxFiles, onFilesChange, validateFile]
  );

  const removeFile = useCallback(
    (index: number) => {
      setLocalError(null);
      onFilesChange(files.filter((_, i) => i !== index));
    },
    [files, onFilesChange]
  );

  const updateDocumentType = useCallback(
    (index: number, documentType: DocumentType) => {
      onFilesChange(
        files.map((entry, i) =>
          i === index ? { ...entry, document_type: documentType } : entry
        )
      );
    },
    [files, onFilesChange]
  );

  const handleDocTypeChange = useCallback(
    (index: number, value: string | null) => {
      if (value !== null) {
        updateDocumentType(index, value as DocumentType);
      }
    },
    [updateDocumentType]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files);
      }
    },
    [addFiles]
  );

  const handleBrowseClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        addFiles(e.target.files);
      }
      // Reset so re-selecting the same file triggers onChange again
      e.target.value = '';
    },
    [addFiles]
  );

  const displayError = error || localError;

  return (
    <div className="flex flex-col gap-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        className={cn(
          'relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors',
          isDragOver
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 hover:bg-muted/30',
          displayError && 'border-destructive/50'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          multiple
          className="hidden"
          onChange={handleFileInputChange}
        />

        <div
          className={cn(
            'flex size-12 items-center justify-center rounded-full bg-muted transition-colors',
            isDragOver && 'bg-primary/10'
          )}
        >
          <Upload
            className={cn(
              'size-6 text-muted-foreground transition-colors',
              isDragOver && 'text-primary'
            )}
          />
        </div>

        <div className="flex flex-col items-center gap-1 text-center">
          <p className="text-sm font-medium text-foreground">
            {isDragOver ? 'Drop files here' : 'Drag & drop files here'}
          </p>
          <p className="text-xs text-muted-foreground">
            or click to browse &mdash; PDF, JPG, PNG &bull; Max 10 MB each
          </p>
        </div>
      </div>

      {/* Error Message */}
      {displayError && (
        <div className="flex items-start gap-2 rounded-md bg-destructive/5 p-3 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{displayError}</span>
        </div>
      )}

      {/* Uploaded Files */}
      {files.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Uploaded Files ({files.length})
          </p>
          <div className="flex flex-col gap-2">
            {files.map((entry, index) => (
              <div
                key={`${entry.file.name}-${index}`}
                className="flex items-center gap-3 rounded-lg border border-border bg-card p-3"
              >
                {/* File icon */}
                <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-muted">
                  <FileText className="size-4 text-muted-foreground" />
                </div>

                {/* File info */}
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <span className="truncate text-sm font-medium text-foreground">
                    {entry.file.name}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatFileSize(entry.file.size)}
                  </span>
                </div>

                {/* Document type selector */}
                <div className="w-40 shrink-0">
                  <Select
                    value={entry.document_type}
                    onValueChange={(value: string | null) =>
                      handleDocTypeChange(index, value)
                    }
                  >
                    <SelectTrigger className="h-7 w-full text-xs">
                      <SelectValue placeholder="Document type" />
                    </SelectTrigger>
                    <SelectContent>
                      {DOCUMENT_TYPES.map((docType) => (
                        <SelectItem key={docType} value={docType}>
                          {DOCUMENT_TYPE_LABELS[docType]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Remove button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-7 shrink-0 text-muted-foreground hover:text-destructive"
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                >
                  <X className="size-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
