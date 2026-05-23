// Shared camera-capture helper used by add_item and edit_photos.
// Usage: const cam = createCameraCapture({ overlayId, videoId, canvasId, fallbackInputId })
// Then: cam.open(), cam.close(), cam.capture(onFile)
function createCameraCapture({ overlayId, videoId, canvasId, fallbackInputId }) {
  let stream = null;

  function open() {
    const overlay = document.getElementById(overlayId);
    overlay.hidden = false;
    overlay.offsetHeight; // force reflow before adding active class
    overlay.classList.add('camera-overlay--active');

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false })
      .then(function (s) {
        stream = s;
        document.getElementById(videoId).srcObject = s;
      })
      .catch(function () {
        close();
        if (fallbackInputId) document.getElementById(fallbackInputId).click();
      });
  }

  function close() {
    if (stream) {
      stream.getTracks().forEach(function (t) { t.stop(); });
      stream = null;
    }
    const overlay = document.getElementById(overlayId);
    overlay.classList.remove('camera-overlay--active');
    overlay.addEventListener('transitionend', function handler() {
      overlay.hidden = true;
      overlay.removeEventListener('transitionend', handler);
    });
  }

  function capture(onFile) {
    const video = document.getElementById(videoId);
    const canvas = document.getElementById(canvasId);
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    close();
    canvas.toBlob(function (blob) {
      onFile(new File([blob], 'photo.jpg', { type: 'image/jpeg' }));
    }, 'image/jpeg', 0.92);
  }

  return { open: open, close: close, capture: capture };
}
