function getImageXYFromEvent(event) {
    let image = event.target;
    const rect = image.getBoundingClientRect(); // Get image's position and dimensions
    const x = event.clientX - rect.left; // x coordinate relative to the image
    const y = event.clientY - rect.top;  // y coordinate relative to the image
  
    // Calculate original image dimensions (if available)
    const originalWidth = image.naturalWidth || image.width; // Use naturalWidth if available, otherwise fallback to current width
    const originalHeight = image.naturalHeight || image.height; // Same for height
  
    // Calculate scaling factors
    const scaleX = originalWidth / rect.width;
    const scaleY = originalHeight / rect.height;
  
    // Calculate original image coordinates
    const originalX = x * scaleX;
    const originalY = y * scaleY;
  
    return [originalX, originalY];
}

window.onload = function() {
  let zoomDiv = document.getElementById('zoom');
  let images = document.querySelectorAll('.report-table img');
  for (var i = 0; i < images.length; i++) {
    images[i].addEventListener('mouseleave', function(event) {
      zoomDiv.style.display = 'none';
    });
    images[i].addEventListener('mouseenter', function(event) {      
      let tr = this.closest('tr');
      let td = null
      for (let img of tr.querySelectorAll('img')) {
        let imgClass = img.className;
        let zoomImg = document.querySelector(`#zoom-${imgClass}`);
        zoomImg.src = img.src;
      }
      zoomDiv.style.display = 'block';
    });
    images[i].addEventListener('mousemove', function(event) {      
      let pos = getImageXYFromEvent(event);

      let tr = this.closest('tr');
      let td = null
      for (let img of tr.querySelectorAll('img')) {
        let imgClass = img.className;
        let zoomImg = document.querySelector(`#zoom-${imgClass}`);
        if (!td) {
          td = zoomImg.parentElement;
          // deduct half the width and height of imgDiff size on screen
          pos = [pos[0] - (td.offsetWidth / 2), pos[1] - (td.offsetHeight / 2)];
        }
        zoomImg.style.left = -pos[0] + 'px';
        zoomImg.style.top = -pos[1] + 'px';
      }
    });
  }
};

