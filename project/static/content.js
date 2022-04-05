function content(e) {
  localStorage.setItem('title', e.getAttribute('title'));
  window.document.location="recommend?movie="+e.getAttribute('title');
  var TheImage = "/project/static/image4.png";
  $('body').css({ 'background-image': "url(" + TheImage + ")" });
}

