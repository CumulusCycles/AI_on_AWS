// Claim form component: 
// handles claim submission with description and accident photo upload
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { claimFormSchema } from '../lib/validation';
import type { ClaimFormData } from '../lib/validation';
import SingleFileUpload from './SingleFileUpload';

interface ClaimFormProps {
  onSubmit: (data: ClaimFormData) => void;
  disabled?: boolean;
}

export default function ClaimForm({ onSubmit, disabled }: ClaimFormProps) {
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
      accident_photo: undefined,
    },
  });

  const accidentPhoto = watch('accident_photo');
  const claimDescription = watch('claim_description');

  // Step 2: File change handler receives file from SingleFileUpload and updates form state
  const handleAccidentPhotoChange = (file: File | null) => {
    setValue('accident_photo', file || undefined, { shouldValidate: true });
  };

  // Step 5: Form submission handler - called after validation passes
  const onFormSubmit = (data: ClaimFormData) => {
    onSubmit(data); // Passes validated data to App component
  };

  return (
    // Step 3: User submits form, Step 4: react-hook-form validates using Zod schema
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      <div>
        <label htmlFor="claim_description" className="block text-sm font-medium text-gray-700 mb-1">
          Description of Claim *
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
          {claimDescription?.length || 0} / 2500 characters
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

      <button
        type="submit"
        disabled={disabled}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {disabled ? 'Processing...' : 'Submit Claim'}
      </button>
    </form>
  );
}