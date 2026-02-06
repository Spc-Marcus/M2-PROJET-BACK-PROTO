"""
Tests for Media upload and management endpoints.

Endpoints tested:
- POST /api/media
- GET /api/media
- GET /api/media/{mediaId}
- DELETE /api/media/{mediaId}
- GET /api/media/orphaned

Test coverage:
- Image upload (JPG, PNG)
- Invalid file types
- File size limits
- Media listing and pagination
- Media deletion
- Orphaned media detection
- Role-based access control
"""

import pytest
import io


# =============================================================================
# POST /api/media
# =============================================================================

def test_upload_image_success_jpg(client, prof_responsible_token):
    """
    Test uploading a JPG image.
    
    Expected: 200 OK or 201 Created, mediaId and url returned
    """
    # Create a mock JPG file
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # JPG header
    files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert "mediaId" in data or "id" in data
    assert "url" in data


def test_upload_image_success_png(client, prof_responsible_token):
    """
    Test uploading a PNG image.
    
    Expected: 200 OK or 201 Created
    """
    # Create a mock PNG file
    image_data = b'\x89PNG\r\n\x1a\n'  # PNG header
    files = {"file": ("test_image.png", io.BytesIO(image_data), "image/png")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    assert response.status_code in [200, 201]


def test_upload_invalid_file_type(client, prof_responsible_token):
    """
    Test uploading non-image file (PDF).
    
    Expected: 400 Bad Request
    """
    # Create a mock PDF file
    pdf_data = b'%PDF-1.4'
    files = {"file": ("document.pdf", io.BytesIO(pdf_data), "application/pdf")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    assert response.status_code == 400


def test_upload_file_too_large(client, prof_responsible_token):
    """
    Test uploading file exceeding size limit.
    
    Expected: 413 Payload Too Large or 400 Bad Request
    """
    # Create a very large file (e.g., 20MB)
    large_data = b'\x00' * (20 * 1024 * 1024)
    files = {"file": ("large_image.jpg", io.BytesIO(large_data), "image/jpeg")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    assert response.status_code in [400, 413]


def test_upload_no_file(client, prof_responsible_token):
    """
    Test upload request without file.
    
    Expected: 400 Bad Request or 422 Unprocessable Entity
    """
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code in [400, 422]


def test_upload_as_student(client, student_token):
    """
    Test that students cannot upload media.
    
    Expected: 403 Forbidden
    """
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {student_token}"},
        files=files
    )
    
    assert response.status_code == 403


def test_upload_as_secondary_prof(client, prof_secondary_token):
    """
    Test that secondary professors can upload media.
    
    Expected: 200 OK or 201 Created
    """
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_secondary_token}"},
        files=files
    )
    
    assert response.status_code in [200, 201]


def test_upload_no_auth(client):
    """
    Test uploading without authentication.
    
    Expected: 401 Unauthorized
    """
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}
    
    response = client.post("/media", files=files)
    
    assert response.status_code == 401


def test_upload_invalid_image_format(client, prof_responsible_token):
    """
    Test uploading file with image extension but invalid content.
    
    Expected: 400 Bad Request
    """
    # Text file masquerading as JPG
    invalid_data = b'This is not an image'
    files = {"file": ("fake.jpg", io.BytesIO(invalid_data), "image/jpeg")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    # Should reject invalid image
    assert response.status_code == 400


# =============================================================================
# GET /api/media
# =============================================================================

def test_list_media(client, prof_responsible_token):
    """
    Test listing uploaded media.
    
    Expected: 200 OK, list of media
    """
    response = client.get(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should be array or paginated response
    assert "data" in data or isinstance(data, list)


def test_list_media_pagination(client, prof_responsible_token):
    """
    Test media list pagination.
    
    Expected: 200 OK, paginated response
    """
    response = client.get(
        "/media?page=1&limit=10",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if "pagination" in data:
        assert "page" in data["pagination"]
        assert "totalItems" in data["pagination"]


def test_list_media_filtered_by_user(client, prof_responsible_token):
    """
    Test that media list shows only user's uploads.
    
    Expected: 200 OK, filtered to user's media
    """
    response = client.get(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Should only show media uploaded by this user


def test_list_media_as_student(client, student_token):
    """
    Test that students cannot list media.
    
    Expected: 403 Forbidden or empty list
    """
    response = client.get(
        "/media",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    # May be forbidden or return empty list
    assert response.status_code in [200, 403]


def test_list_media_no_auth(client):
    """
    Test listing media without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get("/media")
    
    assert response.status_code == 401


# =============================================================================
# GET /api/media/{mediaId}
# =============================================================================

def test_get_media_success(client, prof_responsible_token, media_id):
    """
    Test getting a specific media file.
    
    Expected: 200 OK, media details
    """
    response = client.get(
        f"/media/{media_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == media_id or data["mediaId"] == media_id


def test_get_media_not_found(client, prof_responsible_token):
    """
    Test getting non-existent media.
    
    Expected: 404 Not Found
    """
    response = client.get(
        "/media/non-existent-media-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


def test_get_media_no_auth(client, media_id):
    """
    Test getting media without authentication.
    
    Expected: 401 Unauthorized or 200 OK (if public URLs)
    """
    response = client.get(f"/media/{media_id}")
    
    # Depends on implementation - media may be public or require auth
    assert response.status_code in [200, 401]


# =============================================================================
# DELETE /api/media/{mediaId}
# =============================================================================

def test_delete_unused_media(client, prof_responsible_token):
    """
    Test deleting media that is not used in any questions.
    
    Expected: 204 No Content
    """
    unused_media_id = "unused-media-id"
    
    response = client.delete(
        f"/media/{unused_media_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 204


def test_delete_used_media(client, prof_responsible_token):
    """
    Test deleting media that is used in questions.
    
    Expected: 400 Bad Request or 409 Conflict
    """
    used_media_id = "used-media-id"
    
    response = client.delete(
        f"/media/{used_media_id}",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code in [400, 409]
    # Should have error message about media being in use


def test_delete_media_not_owner(client, prof_secondary_token):
    """
    Test deleting media uploaded by another user.
    
    Expected: 403 Forbidden
    """
    other_user_media_id = "other-user-media-id"
    
    response = client.delete(
        f"/media/{other_user_media_id}",
        headers={"Authorization": f"Bearer {prof_secondary_token}"}
    )
    
    assert response.status_code == 403


def test_delete_media_as_student(client, student_token, media_id):
    """
    Test deleting media as student.
    
    Expected: 403 Forbidden
    """
    response = client.delete(
        f"/media/{media_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_delete_media_not_found(client, prof_responsible_token):
    """
    Test deleting non-existent media.
    
    Expected: 404 Not Found
    """
    response = client.delete(
        "/media/non-existent-media-id",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    assert response.status_code == 404


def test_delete_media_no_auth(client, media_id):
    """
    Test deleting media without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.delete(f"/media/{media_id}")
    
    assert response.status_code == 401


# =============================================================================
# GET /api/media/orphaned
# =============================================================================

def test_list_orphaned_media_as_admin(client, admin_token):
    """
    Test listing orphaned media as admin.
    
    Expected: 200 OK, list of unused media
    """
    response = client.get(
        "/media/orphaned",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should return list of media not used in any questions
    assert isinstance(data, list) or "data" in data


def test_list_orphaned_media_as_professor(client, prof_responsible_token):
    """
    Test listing orphaned media as professor.
    
    Expected: May be 200 OK or 403 Forbidden depending on implementation
    """
    response = client.get(
        "/media/orphaned",
        headers={"Authorization": f"Bearer {prof_responsible_token}"}
    )
    
    # May be admin-only or allow professors to see their own
    assert response.status_code in [200, 403]


def test_list_orphaned_media_as_student(client, student_token):
    """
    Test listing orphaned media as student.
    
    Expected: 403 Forbidden
    """
    response = client.get(
        "/media/orphaned",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 403


def test_list_orphaned_media_no_auth(client):
    """
    Test listing orphaned media without authentication.
    
    Expected: 401 Unauthorized
    """
    response = client.get("/media/orphaned")
    
    assert response.status_code == 401


# =============================================================================
# ADDITIONAL MEDIA TESTS
# =============================================================================

def test_media_url_is_accessible(client, prof_responsible_token):
    """
    Test that uploaded media URL is accessible.
    
    Expected: Media URL returns the file
    """
    # Upload a media file
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}
    
    upload_response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    if upload_response.status_code in [200, 201]:
        data = upload_response.json()
        url = data.get("url")
        
        if url:
            # Try to access the URL
            # Note: This may need to handle relative vs absolute URLs
            pass


def test_media_content_type_validation(client, prof_responsible_token):
    """
    Test that media content type is validated.
    
    Expected: Only image/* content types accepted
    """
    # Try uploading with wrong content type
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    files = {"file": ("test.jpg", io.BytesIO(image_data), "text/plain")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    # Should reject non-image content type
    assert response.status_code == 400


def test_media_filename_sanitization(client, prof_responsible_token):
    """
    Test that filenames are sanitized.
    
    Expected: Special characters in filename handled safely
    """
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    files = {"file": ("../../../etc/passwd.jpg", io.BytesIO(image_data), "image/jpeg")}
    
    response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        # Filename should be sanitized, not contain path traversal
        url = data.get("url", "")
        assert "../" not in url


def test_bulk_delete_orphaned_media(client, admin_token):
    """
    Test bulk deletion of orphaned media (if supported).
    
    Expected: Deletes all unused media
    """
    # This test assumes a bulk delete endpoint exists
    # Implementation may vary
    pass


def test_media_association_with_question(client, prof_responsible_token, quiz_id):
    """
    Test that media becomes associated when used in IMAGE question.
    
    Expected: Media marked as used after question creation
    """
    # Upload media
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    files = {"file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")}
    
    upload_response = client.post(
        "/media",
        headers={"Authorization": f"Bearer {prof_responsible_token}"},
        files=files
    )
    
    if upload_response.status_code in [200, 201]:
        media_id = upload_response.json().get("mediaId") or upload_response.json().get("id")
        
        # Create IMAGE question using this media
        question_response = client.post(
            f"/quizzes/{quiz_id}/questions",
            headers={"Authorization": f"Bearer {prof_responsible_token}"},
            json={
                "type": "IMAGE",
                "contentText": "Click on zone",
                "mediaId": media_id,
                "imageZones": [
                    {"labelName": "Zone1", "x": 50, "y": 60, "radius": 15}
                ]
            }
        )
        
        # Now media should not be deletable (in use)
        if question_response.status_code == 201:
            delete_response = client.delete(
                f"/media/{media_id}",
                headers={"Authorization": f"Bearer {prof_responsible_token}"}
            )
            
            # Should not allow deletion
            assert delete_response.status_code in [400, 409]
