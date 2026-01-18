import React, { useState, useMemo } from 'react';
import { Rocket, CheckCircle, AlertCircle, DollarSign, Clock } from 'lucide-react';
import { workflowService } from '../services/api';

interface WorkflowActivationProps {
  form: any;
  templateId: string;
  estimatedCost: number;
  executionTime: number;
  onSuccess: (data: any) => void;
  onCancel: () => void;
}

const WorkflowActivation: React.FC<WorkflowActivationProps> = ({
  form,
  templateId,
  estimatedCost,
  executionTime,
  onSuccess,
  onCancel
}) => {
  const [inputs, setInputs] = useState<any>(
    form.fields.reduce((acc: any, field: any) => {
      acc[field.name] = field.value || '';
      return acc;
    }, {})
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validationErrors = useMemo(() => {
    const errors: Record<string, string> = {};
    form.fields.forEach((field: any) => {
      if (field.required && !inputs[field.name]) {
        errors[field.name] = 'Ce champ est requis';
      }
      if (field.type === 'number' && inputs[field.name] && isNaN(Number(inputs[field.name]))) {
        errors[field.name] = 'Doit être un nombre';
      }
    });
    return errors;
  }, [inputs, form.fields]);

  const isValid = Object.keys(validationErrors).length === 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await workflowService.activateWorkflow(templateId, inputs);
      onSuccess(result);
    } catch (err: any) {
      console.error('Activation failed:', err);
      setError(err.response?.data?.detail || 'Failed to activate workflow');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 p-6 rounded-lg border border-gray-700 w-full max-w-lg mx-auto shadow-2xl overflow-hidden relative">
      <div className="absolute top-0 left-0 w-1 h-full bg-blue-600"></div>

      <div className="flex items-center space-x-3 mb-6">
        <div className="bg-blue-600/20 p-2 rounded-lg">
          <Rocket className="text-blue-500" size={28} />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">{form.title}</h2>
          <p className="text-sm text-gray-400">{form.description}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-800 p-3 rounded-md border border-gray-700 flex items-center space-x-3">
          <DollarSign className="text-green-500" size={20} />
          <div>
            <p className="text-[10px] uppercase text-gray-500 font-bold">Coût estimé</p>
            <p className="text-white font-medium">{estimatedCost} DZD</p>
          </div>
        </div>
        <div className="bg-gray-800 p-3 rounded-md border border-gray-700 flex items-center space-x-3">
          <Clock className="text-blue-400" size={20} />
          <div>
            <p className="text-[10px] uppercase text-gray-500 font-bold">Temps (moy.)</p>
            <p className="text-white font-medium">{executionTime}s</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {form.fields.map((field: any) => (
          <div key={field.name}>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              {field.label} {field.required && <span className="text-red-500">*</span>}
            </label>
            {field.type === 'select' ? (
              <select
                value={inputs[field.name]}
                onChange={(e) => setInputs({ ...inputs, [field.name]: e.target.value })}
                className={`w-full bg-gray-800 text-white p-2 rounded border ${validationErrors[field.name] ? 'border-red-500' : 'border-gray-600'} focus:ring-2 focus:ring-blue-500`}
                required={field.required}
              >
                <option value="">Select an option</option>
                {field.options.map((opt: any) => (
                  <option key={typeof opt === 'string' ? opt : opt.value} value={typeof opt === 'string' ? opt : opt.value}>
                    {typeof opt === 'string' ? opt : opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={field.type === 'number' ? 'number' : 'text'}
                value={inputs[field.name]}
                onChange={(e) => setInputs({ ...inputs, [field.name]: e.target.value })}
                className={`w-full bg-gray-800 text-white p-2 rounded border ${validationErrors[field.name] ? 'border-red-500' : 'border-gray-600'} focus:ring-2 focus:ring-blue-500`}
                required={field.required}
              />
            )}
            {validationErrors[field.name] && (
              <p className="text-xs text-red-500 mt-1">{validationErrors[field.name]}</p>
            )}
          </div>
        ))}

        {error && (
          <div className="flex items-center space-x-2 text-red-400 bg-red-900/30 p-3 rounded">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <div className="flex space-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || !isValid}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-bold transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
          >
            {loading ? 'Activation...' : 'Activer le Workflow'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default WorkflowActivation;
