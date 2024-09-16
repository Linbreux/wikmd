const tocLinks = document.querySelectorAll('.menu a');
let lastScrollY = window.scrollY; // To keep track of scroll direction
let isManualScroll = false; // Flag to temporarily disable the observer during manual scroll

// Function to set the active TOC link
function setActiveTocItem(tocItem) {
  tocLinks.forEach(link => link.classList.remove('active-toc')); // Remove 'active-toc' class from all links
  if (tocItem) {
    tocItem.classList.add('active-toc'); // Add 'active-toc' class to the clicked item
  }
}

const observer = new IntersectionObserver(entries => {
  // If we're manually scrolling, skip the automatic observer logic
  if (isManualScroll) return;

  let activeEntry = null;
  const scrollingDown = window.scrollY > lastScrollY; // Determine if scrolling down
  lastScrollY = window.scrollY;

  entries.forEach(entry => {
    if (entry.isIntersecting) {
      if (scrollingDown) {
        // Prefer entry that's coming into view when scrolling down
        if (!activeEntry || entry.boundingClientRect.top < activeEntry.boundingClientRect.top) {
          activeEntry = entry;
        }
      } else {
        // Prefer entry that's still partially visible or leaving the viewport when scrolling up
        if (!activeEntry || entry.boundingClientRect.top > activeEntry.boundingClientRect.top) {
          activeEntry = entry;
        }
      }
    }
  });

  // Handle the case where no headers are intersecting (e.g., scrolling too fast)
  if (!activeEntry) {
    entries.forEach(entry => {
      if (scrollingDown && entry.boundingClientRect.top >= 0) {
        activeEntry = entry;
        return;
      } else if (!scrollingDown && entry.boundingClientRect.bottom <= window.innerHeight) {
        activeEntry = entry;
        return;
      }
    });
  }

  // Highlight the active TOC link based on the current header in view
  if (activeEntry) {
    const tocItem = document.querySelector(`#toc-${activeEntry.target.id}`);
    setActiveTocItem(tocItem);
  }
}, {
  root: null,
  rootMargin: '0px',
  threshold: 1 // Adjusted threshold for quicker detection
});

document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(header => {
  observer.observe(header);
});

// Add click event listeners to TOC links
tocLinks.forEach(link => {
  link.addEventListener('click', (event) => {
    event.preventDefault(); // Prevent the default jump behavior
    const targetId = link.getAttribute('href').slice(1); // Get the target ID from the href attribute
    const targetElement = document.getElementById(targetId);

    // Temporarily disable the IntersectionObserver
    isManualScroll = true;
    
    // Scroll to the target element
    targetElement.scrollIntoView({
      behavior: 'smooth'
    });

    // Set the clicked TOC link as active
    setActiveTocItem(link);

    // Re-enable the IntersectionObserver after a short delay to allow the scroll to finish
    setTimeout(() => {
      isManualScroll = false;
    }, 1000); // Adjust delay time as needed to match scroll speed
  });
});

