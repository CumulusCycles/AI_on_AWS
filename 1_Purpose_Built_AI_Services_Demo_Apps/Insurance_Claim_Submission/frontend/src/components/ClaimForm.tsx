import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { claimFormSchema, ClaimFormData } from '../lib/validation';
import FileUpload from './FileUpload';
import SingleFileUpload from './SingleFileUpload';

interface ClaimFormProps {
  onSubmit: (data: ClaimFormData) => Promise<void>;
  disabled?: boolean;
  processingStatus?: Record<string, string>;
  isProcessed?: boolean;
}

export default function ClaimForm({ onSubmit, disabled, processingStatus, isProcessed = false }: ClaimFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<ClaimFormData>({
    resolver: zodResolver(claimFormSchema),
    defaultValues: {
      claim_description: '',
      accident_photo: null,
      insurance_forms: [],
    },
  });

  const accidentPhoto = watch('accident_photo');
  const insuranceForms = watch('insurance_forms') || [];

  const handleAccidentPhotoChange = (file: File | null) => {
    setValue('accident_photo', file as File, { shouldValidate: true });
  };

  const handleInsuranceFormsChange = (newFiles: File[]) => {
    setValue('insurance_forms', newFiles, { shouldValidate: true });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="claim_description" className="block text-sm font-medium text-gray-700 mb-1">
          Claim Description *
        </label>
        <textarea
          {...register('claim_description')}
          id="claim_description"
          rows={10}
          disabled={disabled}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
          placeholder="Enter your claim description here..."
        />
        {errors.claim_description && (
          <p className="mt-1 text-sm text-red-600">{errors.claim_description.message}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          {watch('claim_description')?.length || 0} / 3000 characters
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Accident Photo *
        </label>
        <SingleFileUpload
          file={accidentPhoto}
          onFileChange={handleAccidentPhotoChange}
          disabled={disabled}
          error={errors.accident_photo?.message}
          accept=".png,.jpg,.jpeg,.gif,.bmp"
          label="Drag and drop accident photo here, or click to select"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Insurance Forms * (PDF or PNG)
        </label>
        <FileUpload
          files={insuranceForms}
          onFilesChange={handleInsuranceFormsChange}
          disabled={disabled}
          error={errors.insurance_forms?.message}
        />
      </div>

      {processingStatus && Object.keys(processingStatus).length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <p className="text-sm font-semibold text-blue-900 mb-2">Processing Status:</p>
          <div className="space-y-1">
            {Object.entries(processingStatus).map(([key, status]) => (
              <div key={key} className="text-xs">
                <span className="font-medium">{key}:</span>{' '}
                <span className={status.includes('error') ? 'text-red-600' : 'text-green-600'}>
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={disabled || isProcessed}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isProcessed ? 'Claim Processed' : disabled ? 'Processing...' : 'Submit Claim'}
      </button>
    </form>
  );
}

