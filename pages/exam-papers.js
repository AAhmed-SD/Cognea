import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout/Layout';
import { 
  Upload, 
  FileText, 
  Folder, 
  Share2, 
  Search, 
  Plus, 
  Trash2, 
  Eye,
  Download,
  CheckCircle,
  AlertCircle,
  Clock,
  BookOpen,
  Users,
  Lock,
  Globe
} from 'lucide-react';

const ExamPapers = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('upload');
  const [uploading, setUploading] = useState(false);
  const [papers, setPapers] = useState([]);
  const [collections, setCollections] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateCollection, setShowCreateCollection] = useState(false);
  const [newCollection, setNewCollection] = useState({ name: '', description: '', isPublic: false });
  const fileInputRef = useRef();

  useEffect(() => {
    if (user) {
      fetchPapers();
      fetchCollections();
    }
  }, [user]);

  const fetchPapers = async () => {
    try {
      const response = await fetch('/api/exam-papers/papers', {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });
      const data = await response.json();
      setPapers(data.papers || []);
    } catch (error) {
      console.error('Error fetching papers:', error);
    }
  };

  const fetchCollections = async () => {
    try {
      const response = await fetch('/api/exam-papers/collections', {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });
      const data = await response.json();
      setCollections(data.collections || []);
    } catch (error) {
      console.error('Error fetching collections:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch('/api/exam-papers/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.token}`
        },
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.ok) {
        const result = await response.json();
        setSelectedFile(null);
        setUploadProgress(0);
        fetchPapers();
        
        // Show success message
        alert(`Successfully processed ${result.questions_count} questions!`);
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleCreateCollection = async () => {
    try {
      const formData = new FormData();
      formData.append('name', newCollection.name);
      formData.append('description', newCollection.description);
      formData.append('is_public', newCollection.isPublic);

      const response = await fetch('/api/exam-papers/collections', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.token}`
        },
        body: formData
      });

      if (response.ok) {
        setNewCollection({ name: '', description: '', isPublic: false });
        setShowCreateCollection(false);
        fetchCollections();
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create collection');
      }
    } catch (error) {
      console.error('Error creating collection:', error);
      alert(`Failed to create collection: ${error.message}`);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'processing':
        return 'text-yellow-600 bg-yellow-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Exam Papers</h1>
          <p className="text-gray-600">
            Upload exam papers and let AI extract questions, generate solutions, and create study materials.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'upload', label: 'Upload Papers', icon: Upload },
              { id: 'papers', label: 'My Papers', icon: FileText },
              { id: 'collections', label: 'Collections', icon: Folder },
              { id: 'shared', label: 'Shared', icon: Share2 }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="max-w-2xl mx-auto">
              <div className="text-center mb-8">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Upload Exam Paper
                </h2>
                <p className="text-gray-600">
                  Upload a PDF or image of an exam paper. Our AI will extract questions and generate solutions.
                </p>
              </div>

              {/* File Upload Area */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.tiff"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                
                {!selectedFile ? (
                  <div onClick={() => fileInputRef.current?.click()}>
                    <Upload className="w-8 h-8 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-2">
                      Click to select a file or drag and drop
                    </p>
                    <p className="text-sm text-gray-500">
                      PDF, JPG, PNG, TIFF up to 10MB
                    </p>
                  </div>
                ) : (
                  <div>
                    <FileText className="w-8 h-8 text-blue-500 mx-auto mb-4" />
                    <p className="text-gray-900 font-medium mb-1">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500 mb-4">
                      {formatFileSize(selectedFile.size)}
                    </p>
                    <div className="flex space-x-3 justify-center">
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                      >
                        Remove
                      </button>
                      <button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                      >
                        {uploading ? 'Processing...' : 'Upload & Process'}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Upload Progress */}
              {uploading && (
                <div className="mt-6">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Processing...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* Legal Notice */}
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <div className="flex">
                  <AlertCircle className="w-5 h-5 text-blue-400 mt-0.5 mr-3" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Legal Notice</p>
                    <p>
                      By uploading, you confirm you own or have permission to use this content for personal educational use only.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Papers Tab */}
        {activeTab === 'papers' && (
          <div className="space-y-6">
            {/* Search and Filters */}
            <div className="flex items-center space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search papers..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Papers Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {papers
                .filter(paper => 
                  paper.file_name.toLowerCase().includes(searchTerm.toLowerCase())
                )
                .map((paper) => (
                  <div key={paper.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-8 h-8 text-blue-500" />
                        <div>
                          <h3 className="font-medium text-gray-900 truncate">
                            {paper.file_name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {formatFileSize(paper.file_size)}
                          </p>
                        </div>
                      </div>
                      {getStatusIcon(paper.processing_status)}
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Questions:</span>
                        <span className="font-medium">{paper.extracted_questions_count}</span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Uploaded:</span>
                        <span className="text-gray-900">{formatDate(paper.upload_date)}</span>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Status:</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(paper.processing_status)}`}>
                          {paper.processing_status}
                        </span>
                      </div>
                    </div>

                    <div className="mt-4 flex space-x-2">
                      <button className="flex-1 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100">
                        <Eye className="w-4 h-4 inline mr-1" />
                        View
                      </button>
                      <button className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-red-600">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
            </div>

            {papers.length === 0 && (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No papers uploaded yet</h3>
                <p className="text-gray-600 mb-4">
                  Upload your first exam paper to get started with AI-powered question extraction.
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Upload Paper
                </button>
              </div>
            )}
          </div>
        )}

        {/* Collections Tab */}
        {activeTab === 'collections' && (
          <div className="space-y-6">
            {/* Header with Create Button */}
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">My Collections</h2>
              <button
                onClick={() => setShowCreateCollection(true)}
                className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                <span>New Collection</span>
              </button>
            </div>

            {/* Collections Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {collections.map((collection) => (
                <div key={collection.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <Folder className="w-8 h-8 text-purple-500" />
                      <div>
                        <h3 className="font-medium text-gray-900">{collection.name}</h3>
                        <p className="text-sm text-gray-500">
                          {collection.questions_count} questions
                        </p>
                      </div>
                    </div>
                    {collection.is_public ? (
                      <Globe className="w-4 h-4 text-green-500" />
                    ) : (
                      <Lock className="w-4 h-4 text-gray-400" />
                    )}
                  </div>

                  {collection.description && (
                    <p className="text-sm text-gray-600 mb-4">{collection.description}</p>
                  )}

                  <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                    <span>Created {formatDate(collection.created_at)}</span>
                  </div>

                  <div className="flex space-x-2">
                    <button className="flex-1 px-3 py-2 text-sm font-medium text-purple-600 bg-purple-50 rounded-md hover:bg-purple-100">
                      <BookOpen className="w-4 h-4 inline mr-1" />
                      Open
                    </button>
                    <button className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-blue-600">
                      <Share2 className="w-4 h-4" />
                    </button>
                    <button className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-red-600">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {collections.length === 0 && (
              <div className="text-center py-12">
                <Folder className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No collections yet</h3>
                <p className="text-gray-600 mb-4">
                  Create collections to organize your questions and share them with others.
                </p>
                <button
                  onClick={() => setShowCreateCollection(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Create Collection
                </button>
              </div>
            )}
          </div>
        )}

        {/* Shared Tab */}
        {activeTab === 'shared' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Shared Collections</h2>
            
            <div className="text-center py-12">
              <Share2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No shared collections</h3>
              <p className="text-gray-600">
                Collections shared with you will appear here.
              </p>
            </div>
          </div>
        )}

        {/* Create Collection Modal */}
        {showCreateCollection && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Collection</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Collection Name
                  </label>
                  <input
                    type="text"
                    value={newCollection.name}
                    onChange={(e) => setNewCollection({...newCollection, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter collection name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    value={newCollection.description}
                    onChange={(e) => setNewCollection({...newCollection, description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    rows="3"
                    placeholder="Describe your collection"
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="isPublic"
                    checked={newCollection.isPublic}
                    onChange={(e) => setNewCollection({...newCollection, isPublic: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="isPublic" className="ml-2 block text-sm text-gray-900">
                    Make this collection public
                  </label>
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateCollection(false)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCollection}
                  disabled={!newCollection.name.trim()}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default ExamPapers; 