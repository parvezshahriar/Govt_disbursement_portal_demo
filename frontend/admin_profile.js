// admin_profile.js - User Profile Management

let currentUserId = null;
let isEditMode = false;
let originalProfileData = {};

/**
 * Initialize the profile page on load
 */
document.addEventListener('DOMContentLoaded', function () {
    console.log('[PROFILE_INIT] Initializing profile page');

    // Step 1: Get user info from localStorage
    const userId = localStorage.getItem('userId');
    const username = localStorage.getItem('username');
    const userRole = localStorage.getItem('userRole');

    if (!userId) {
        console.log('[PROFILE_INIT] Step 1: No user logged in, redirecting to login');
        showError('AUTH_FAILED', 'Please log in first', false);
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
        return;
    }

    console.log('[PROFILE_INIT] Step 2: User found - ID: ' + userId + ', Username: ' + username);

    currentUserId = parseInt(userId);

    // Step 3: Load profile data
    loadProfileData();
});

/**
 * Load user profile data from the backend
 */
function loadProfileData() {
    console.log('[LOAD_PROFILE] Step 1: Fetching profile data for user_id: ' + currentUserId);

    try {
        // Step 2: Validate user ID
        if (!currentUserId || currentUserId < 1) {
            console.log('[LOAD_PROFILE] Step 2: Invalid user ID');
            showError('VALIDATION_FAILED', 'Invalid user ID', false);
            return;
        }

        // Step 3: Make API request
        console.log('[LOAD_PROFILE] Step 3: Making API request to /user-info/' + currentUserId);

        fetch(`http://127.0.0.1:8000/user-info/${currentUserId}`)
            .then(response => {
                console.log('[LOAD_PROFILE] Step 4: Received response with status: ' + response.status);

                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('[LOAD_PROFILE] Step 5: Profile data received successfully');
                originalProfileData = JSON.parse(JSON.stringify(data));
                populateProfileForm(data);
                console.log('[LOAD_PROFILE] Step 6: Profile form populated');

                // Step 7: Load user images
                loadUserImages();
            })
            .catch(error => {
                console.log('[LOAD_PROFILE] Step 5: Error caught - ' + error.message);

                if (error.message.includes('Failed to fetch')) {
                    showError('SERVER_NOT_CONNECTED', 'Cannot reach server', false);
                } else {
                    showError('UNKNOWN_ERROR', 'Error loading profile: ' + error.message, false);
                }
            });
    } catch (error) {
        console.log('[LOAD_PROFILE] ERROR: ' + error.message);
        showError('UNKNOWN_ERROR', error.message, false);
    }
}

/**
 * Populate form fields with profile data
 */
function populateProfileForm(data) {
    console.log('[POPULATE_FORM] Step 1: Starting form population');

    try {
        // Step 2: Set basic user info
        const username = localStorage.getItem('username');
        const userRole = localStorage.getItem('userRole');

        document.getElementById('profile-name').textContent =
            (data.first_name || username) + ' ' + (data.last_name || '');

        // Set Employee ID instead of DOB
        const employeeIdDisplay = document.getElementById('profile-employee-id-display');
        if (employeeIdDisplay) {
            if (data.employee_id) {
                employeeIdDisplay.textContent = `ID: ${data.employee_id}`;
                employeeIdDisplay.style.display = 'block';
            } else {
                employeeIdDisplay.style.display = 'none';
            }
        }

        document.getElementById('profile-role').textContent = userRole || 'User';

        // Step 3: Populate form fields
        if (data.first_name) document.getElementById('firstName').value = data.first_name;
        if (data.last_name) document.getElementById('lastName').value = data.last_name;
        if (data.phone) document.getElementById('phone').value = data.phone;
        if (data.date_of_birth) document.getElementById('dob').value = data.date_of_birth;
        if (data.gender) document.getElementById('gender').value = data.gender;
        if (data.employee_id) document.getElementById('employeeId').value = data.employee_id;
        if (data.department) document.getElementById('department').value = data.department;
        if (data.position) document.getElementById('position').value = data.position;
        if (data.office_address) document.getElementById('address').value = data.office_address;

        // Step 4: Set avatar if exists
        if (data.avatar_url) {
            let avatarUrl = data.avatar_url;
            // If it's a relative URL, prepend the API base URL
            if (!avatarUrl.startsWith('http')) {
                avatarUrl = 'http://127.0.0.1:8000' + avatarUrl;
            }
            console.log('[POPULATE_FORM] Step 4: Setting avatar URL to: ' + avatarUrl);
            document.getElementById('card-profile-avatar').src = avatarUrl;
        } else {
            console.log('[POPULATE_FORM] Step 4: No avatar URL found');
        }

        console.log('[POPULATE_FORM] Step 5: Form populated successfully');
    } catch (error) {
        console.log('[POPULATE_FORM] ERROR: ' + error.message);
        showError('UNKNOWN_ERROR', 'Error populating form: ' + error.message, false);
    }
}

/**
 * Toggle edit mode on/off
 */
function toggleEditMode() {
    console.log('[EDIT_MODE] Step 1: Toggling edit mode, current state: ' + isEditMode);

    try {
        isEditMode = !isEditMode;

        // Step 2: Get all form fields
        const formFields = document.querySelectorAll('.form-group input, .form-group select, .form-group textarea');
        const editBadge = document.getElementById('edit-badge');
        const actionButtons = document.getElementById('action-buttons');
        const editButton = document.querySelector('.btn-action.primary');

        console.log('[EDIT_MODE] Step 2: Found ' + formFields.length + ' form fields');

        // Step 3: Enable/disable fields
        if (isEditMode) {
            console.log('[EDIT_MODE] Step 3: Enabling edit mode');
            formFields.forEach(field => {
                field.disabled = false;
            });
            editBadge.style.display = 'inline-block';
            actionButtons.style.display = 'flex';
            editButton.innerHTML = '<i class="fas fa-times"></i> Cancel Edit';
            editButton.classList.add('danger');
            console.log('[EDIT_MODE] Step 4: Edit mode enabled');
        } else {
            console.log('[EDIT_MODE] Step 3: Disabling edit mode');
            formFields.forEach(field => {
                field.disabled = true;
            });
            editBadge.style.display = 'none';
            actionButtons.style.display = 'none';
            editButton.innerHTML = '<i class="fas fa-edit"></i> Edit Profile';
            editButton.classList.remove('danger');
            cancelEdit();
            console.log('[EDIT_MODE] Step 4: Edit mode disabled');
        }
    } catch (error) {
        console.log('[EDIT_MODE] ERROR: ' + error.message);
        showError('UNKNOWN_ERROR', error.message, false);
    }
}

/**
 * Save profile changes to the database
 */
function saveProfile() {
    console.log('[SAVE_PROFILE] Step 1: Starting profile save');

    try {
        // Step 2: Validate user ID
        if (!currentUserId || currentUserId < 1) {
            console.log('[SAVE_PROFILE] Step 2: Invalid user ID');
            showError('VALIDATION_FAILED', 'Invalid user ID', false);
            return;
        }

        // Step 3: Collect form data
        console.log('[SAVE_PROFILE] Step 3: Collecting form data');

        const profileData = {
            first_name: document.getElementById('firstName').value || null,
            last_name: document.getElementById('lastName').value || null,
            phone: document.getElementById('phone').value || null,
            date_of_birth: document.getElementById('dob').value || null,
            gender: document.getElementById('gender').value || null,
            employee_id: document.getElementById('employeeId').value || null,
            department: document.getElementById('department').value || null,
            position: document.getElementById('position').value || null,
            office_address: document.getElementById('address').value || null
        };

        console.log('[SAVE_PROFILE] Step 4: Form data collected');

        // Step 5: Validate data
        if (!profileData.first_name && !profileData.last_name) {
            console.log('[SAVE_PROFILE] Step 5: Validation failed - no name provided');
            showError('VALIDATION_FAILED', 'Please enter at least a first or last name', false);
            return;
        }

        console.log('[SAVE_PROFILE] Step 6: Validation passed');

        // Step 7: Send to API
        console.log('[SAVE_PROFILE] Step 7: Sending request to /user-info/' + currentUserId);

        fetch(`http://127.0.0.1:8000/user-info/${currentUserId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        })
            .then(response => {
                console.log('[SAVE_PROFILE] Step 8: Received response with status: ' + response.status);

                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('[SAVE_PROFILE] Step 9: Profile saved successfully');
                originalProfileData = JSON.parse(JSON.stringify(data));

                // Step 10: Show success message
                showError('UPDATE_SUCCESS', 'Profile updated successfully!', true);
                console.log('[SAVE_PROFILE] Step 11: Success popup shown');

                // Step 11: Exit edit mode after 2 seconds
                setTimeout(() => {
                    isEditMode = true; // Set to true so toggle will set it to false
                    toggleEditMode();
                    loadProfileData();
                }, 1000);
            })
            .catch(error => {
                console.log('[SAVE_PROFILE] Step 9: Error caught - ' + error.message);

                if (error.message.includes('Failed to fetch')) {
                    showError('SERVER_NOT_CONNECTED', 'Cannot reach server', false);
                } else if (error.message.includes('400')) {
                    showError('VALIDATION_FAILED', 'Invalid data format', false);
                } else {
                    showError('UPDATE_FAILED', 'Error saving profile: ' + error.message, false);
                }
            });
    } catch (error) {
        console.log('[SAVE_PROFILE] ERROR: ' + error.message);
        showError('UNKNOWN_ERROR', error.message, false);
    }
}

/**
 * Cancel edit mode and reset form
 */
function cancelEdit() {
    console.log('[CANCEL_EDIT] Step 1: Canceling edit mode');

    try {
        // Step 2: Reset form to original data
        console.log('[CANCEL_EDIT] Step 2: Resetting form to original data');

        document.getElementById('firstName').value = originalProfileData.first_name || '';
        document.getElementById('lastName').value = originalProfileData.last_name || '';
        document.getElementById('phone').value = originalProfileData.phone || '';
        document.getElementById('dob').value = originalProfileData.date_of_birth || '';
        document.getElementById('gender').value = originalProfileData.gender || '';
        document.getElementById('employeeId').value = originalProfileData.employee_id || '';
        document.getElementById('department').value = originalProfileData.department || '';
        document.getElementById('position').value = originalProfileData.position || '';
        document.getElementById('address').value = originalProfileData.office_address || '';

        console.log('[CANCEL_EDIT] Step 3: Form reset complete');
    } catch (error) {
        console.log('[CANCEL_EDIT] ERROR: ' + error.message);
        showError('UNKNOWN_ERROR', error.message, false);
    }
}

/**
 * Handle avatar upload - now integrated with backend image storage
 */
function handleAvatarUpload(event) {
    console.log('[AVATAR_UPLOAD] Step 1: Starting avatar upload');

    try {
        const file = event.target.files[0];

        // Step 2: Validate file
        if (!file) {
            console.log('[AVATAR_UPLOAD] Step 2: No file selected');
            return;
        }

        console.log('[AVATAR_UPLOAD] Step 3: File selected - ' + file.name + ' (' + file.size + ' bytes)');

        // Step 4: Check file type
        if (!file.type.startsWith('image/')) {
            console.log('[AVATAR_UPLOAD] Step 4: Invalid file type');
            showError('FILE_UPLOAD_FAILED', 'Please select an image file', false);
            return;
        }

        // Step 5: Check file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            console.log('[AVATAR_UPLOAD] Step 5: File too large');
            showError('FILE_UPLOAD_FAILED', 'Image size must be less than 10MB', false);
            return;
        }

        // Step 6: Upload to backend
        uploadImageToBackend(file, true);

    } catch (error) {
        console.log('[AVATAR_UPLOAD] ERROR: ' + error.message);
        showError('FILE_UPLOAD_FAILED', error.message, false);
    }
}

/**
 * Upload image to backend using the image API
 */
function uploadImageToBackend(file, isProfileAvatar = false) {
    console.log('[BACKEND_UPLOAD] Step 1: Uploading image to backend - ' + file.name);

    try {
        // Show uploading status
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', currentUserId);
        formData.append('description', 'Profile picture uploaded on ' + new Date().toLocaleDateString());

        console.log('[BACKEND_UPLOAD] Step 2: Sending to /image-upload endpoint');

        fetch('http://127.0.0.1:8000/image-upload', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                console.log('[BACKEND_UPLOAD] Step 3: Response received - ' + response.status);

                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('[BACKEND_UPLOAD] Step 4: Upload successful - Image ID: ' + data.image_id);

                // Step 5: Show preview and update avatar if this is a profile picture
                if (isProfileAvatar) {
                    const imageUrl = 'http://127.0.0.1:8000' + data.view_url;
                    document.getElementById('card-profile-avatar').src = imageUrl;
                    showUploadMessage('✓ Profile picture updated successfully!', 'success');

                    // NEW: Cleanup old images - Keep only the new one
                    cleanupOldImages(data.image_id);
                } else {
                    // Start 6: Reload gallery if not profile avatar (otherwise cleanup does it)
                    loadUserImages();
                }

                // Step 7: Clear file input
                document.getElementById('avatar-input').value = '';
            })
            .catch(error => {
                console.log('[BACKEND_UPLOAD] Step 4: Error - ' + error.message);
                showUploadMessage('✗ Upload failed: ' + error.message, 'error');
            });

    } catch (error) {
        console.log('[BACKEND_UPLOAD] ERROR: ' + error.message);
        showUploadMessage('✗ Upload error: ' + error.message, 'error');
    }
}

/**
 * Load user's profile images from backend
 */
function loadUserImages() {
    console.log('[LOAD_USER_IMAGES] Step 1: Fetching user images for user_id: ' + currentUserId);

    const galleryDiv = document.getElementById('profile-gallery');
    const loadingDiv = document.getElementById('gallery-loading');

    if (!galleryDiv) {
        console.log('[LOAD_USER_IMAGES] Gallery div not found');
        return;
    }

    loadingDiv.style.display = 'block';
    galleryDiv.innerHTML = '';

    try {
        fetch(`http://127.0.0.1:8000/user-images/${currentUserId}`)
            .then(response => {
                console.log('[LOAD_USER_IMAGES] Step 2: Response - ' + response.status);
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('[LOAD_USER_IMAGES] Step 3: Received ' + data.total_images + ' images');
                loadingDiv.style.display = 'none';

                if (data.total_images === 0) {
                    galleryDiv.innerHTML = `
                        <div class="empty-gallery">
                            <i class="fas fa-image"></i>
                            <p>No profile pictures yet</p>
                            <small>Click the camera icon on your avatar to upload one</small>
                        </div>
                    `;
                    return;
                }

                // Step 4: Display images
                data.images.forEach(image => {
                    const imageCard = document.createElement('div');
                    imageCard.className = 'image-card';
                    imageCard.innerHTML = `
                        <img src="http://127.0.0.1:8000${image.view_url}" alt="${image.original_filename}" class="image-thumbnail">
                        <div class="image-card-overlay">
                            <button onclick="viewImage(${image.id})" class="image-action-btn" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button onclick="setAsProfilePicture(${image.id})" class="image-action-btn" title="Set as profile">
                                <i class="fas fa-check"></i>
                            </button>
                            <button onclick="deleteImage(${image.id})" class="image-action-btn delete" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                        <div class="image-info">
                            <small>${new Date(image.created_at).toLocaleDateString()}</small>
                        </div>
                    `;
                    galleryDiv.appendChild(imageCard);
                });

                console.log('[LOAD_USER_IMAGES] Step 5: Gallery rendered');
            })
            .catch(error => {
                console.log('[LOAD_USER_IMAGES] Step 3: Error - ' + error.message);
                loadingDiv.style.display = 'none';
                galleryDiv.innerHTML = `
                    <div class="empty-gallery">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Failed to load images</p>
                        <small>${error.message}</small>
                    </div>
                `;
            });
    } catch (error) {
        console.log('[LOAD_USER_IMAGES] ERROR: ' + error.message);
        loadingDiv.style.display = 'none';
    }
}

/**
 * Set an image as the profile picture
 */
function setAsProfilePicture(imageId) {
    console.log('[SET_PROFILE_PIC] Setting image ' + imageId + ' as profile picture');

    try {
        fetch(`http://127.0.0.1:8000/image-info/${imageId}`)
            .then(response => response.json())
            .then(data => {
                console.log('[SET_PROFILE_PIC] Updating avatar with image URL');
                document.getElementById('card-profile-avatar').src = 'http://127.0.0.1:8000' + data.view_url;
                showUploadMessage('✓ Profile picture updated!', 'success');
            })
            .catch(error => {
                console.log('[SET_PROFILE_PIC] Error: ' + error.message);
                showUploadMessage('✗ Failed to set profile picture', 'error');
            });
    } catch (error) {
        console.log('[SET_PROFILE_PIC] ERROR: ' + error.message);
    }
}

/**
 * View image in a modal
 */
function viewImage(imageId) {
    console.log('[VIEW_IMAGE] Viewing image ' + imageId);

    try {
        fetch(`http://127.0.0.1:8000/image-info/${imageId}`)
            .then(response => response.json())
            .then(data => {
                const modal = document.createElement('div');
                modal.className = 'image-modal';
                modal.innerHTML = `
                    <div class="image-modal-content">
                        <button class="close-modal" onclick="this.closest('.image-modal').remove()">&times;</button>
                        <img src="http://127.0.0.1:8000${data.view_url}" alt="">
                        <div class="image-details">
                            <p><strong>Filename:</strong> ${data.original_filename}</p>
                            <p><strong>Size:</strong> ${(data.file_size / 1024).toFixed(2)} KB</p>
                            <p><strong>Type:</strong> ${data.mime_type}</p>
                            <p><strong>Uploaded:</strong> ${new Date(data.created_at).toLocaleString()}</p>
                            ${data.description ? `<p><strong>Description:</strong> ${data.description}</p>` : ''}
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
                modal.addEventListener('click', function (e) {
                    if (e.target === this) this.remove();
                });
            });
    } catch (error) {
        console.log('[VIEW_IMAGE] ERROR: ' + error.message);
    }
}

/**
 * Delete an image
 */
function deleteImage(imageId, silent = false) {
    console.log('[DELETE_IMAGE] Deleting image ' + imageId);

    if (!silent && !confirm('Are you sure you want to delete this image?')) {
        console.log('[DELETE_IMAGE] Deletion cancelled');
        return;
    }

    try {
        fetch(`http://127.0.0.1:8000/image/${imageId}`, {
            method: 'DELETE'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('[DELETE_IMAGE] Image deleted successfully');
                if (!silent) showUploadMessage('✓ Image deleted successfully', 'success');
                loadUserImages();
            })
            .catch(error => {
                console.log('[DELETE_IMAGE] Error: ' + error.message);
                showUploadMessage('✗ Failed to delete image: ' + error.message, 'error');
            });
    } catch (error) {
        console.log('[DELETE_IMAGE] ERROR: ' + error.message);
    }
}

/**
 * Cleanup old images, keeping only the specified one
 */
function cleanupOldImages(keepImageId) {
    console.log('[CLEANUP] Removing old images, keeping: ' + keepImageId);

    fetch(`http://127.0.0.1:8000/user-images/${currentUserId}`)
        .then(r => r.json())
        .then(data => {
            if (data.images && data.images.length > 0) {
                // Find images to delete
                const imagesToDelete = data.images.filter(img => img.id !== keepImageId);
                console.log('[CLEANUP] Found ' + imagesToDelete.length + ' old images to delete');

                // Delete them one by one
                imagesToDelete.forEach(img => {
                    deleteImage(img.id, true); // true for silent deletion
                });

                // Refresh gallery after short delay to allow deletions to process
                setTimeout(loadUserImages, 1000);
            } else {
                loadUserImages();
            }
        })
        .catch(e => console.error('[CLEANUP] Error fetching images: ', e));
}

/**
 * Show upload message
 */
function showUploadMessage(message, type) {
    const messageDiv = document.getElementById('upload-message');
    if (!messageDiv) return;

    messageDiv.textContent = message;
    messageDiv.className = 'message-box ' + type;
    messageDiv.style.display = 'block';

    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 1500);
    }
}

/**
 * Change password (placeholder function)
 */
function changePassword() {
    console.log('[CHANGE_PASSWORD] Step 1: Password change initiated');
    showError('FEATURE_INFO', 'Password change feature coming soon', false);
}
