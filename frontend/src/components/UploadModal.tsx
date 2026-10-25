import React, { useState, useRef } from 'react';
import { Upload, X, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (dataset: any) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState<string>('');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      if (!datasetName) {
        setDatasetName(droppedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!datasetName) {
        setDatasetName(selectedFile.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please choose a dataset file to upload.');
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    if (datasetName) {
      formData.append('dataset_name', datasetName);
    }

    try {
      const res = await axios.post('/api/v1/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setIsUploading(false);
      onUploadSuccess(res.data);
      onClose();
    } catch (err: any) {
      setIsUploading(false);
      setError(err.response?.data?.detail || 'Failed to upload and profile dataset.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Title */}
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Upload New Dataset</h2>
            <p className="text-xs text-slate-400">
              Supports CSV, Excel (.xlsx/.xls), JSON, and Parquet.
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Drag & Drop Zone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
              file
                ? 'border-indigo-500 bg-indigo-950/20'
                : 'border-slate-700 hover:border-slate-600 bg-slate-800/40'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls,.json,.parquet"
              onChange={handleFileSelect}
              className="hidden"
            />
            {file ? (
              <div className="flex flex-col items-center space-y-2">
                <FileText className="w-8 h-8 text-indigo-400" />
                <span className="text-xs font-semibold text-white">{file.name}</span>
                <span className="text-[11px] text-slate-400">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </span>
                <span className="text-[11px] text-indigo-400 underline">Click to change file</span>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-2">
                <Upload className="w-8 h-8 text-slate-500" />
                <span className="text-xs font-medium text-slate-300">
                  Drag & drop your dataset here, or <span className="text-indigo-400 underline">browse</span>
                </span>
                <span className="text-[11px] text-slate-500">
                  Any schema or structure; automatic column & type detection
                </span>
              </div>
            )}
          </div>

          {/* Dataset Name Input */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Dataset Name (Optional)
            </label>
            <input
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="e.g. Q4 Regional Financials"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isUploading}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !file}
              className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg transition shadow-md shadow-indigo-600/30"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Profiling & Generating BI...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Ingest & Generate Dashboard</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
