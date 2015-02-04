/************************
qscan jQuery

* infinite scroll for
  the qscan main page

  * AJAX to log scanning 
  decisions

by danny goldstein 2014
*************************/

jQuery(document).ready(function() {

  // Always start from the top.

  $(window).on('beforeunload', function() {
    $(window).scrollTop(0);
  });
  
  // When there are no objects left on the server, cease all AJAX
  // calls to fetch new objects by toggling the fetchobjects
  // variable.

  var fetchobjects = true;

  // Set up the page with an initial fetch.
  
  fetchScanObjectsAjax();

  // When you hit the bottom of the page, load more crap to scan.
  // The 'ajaxready' variable prevents multiple AJAX calls from
  // being launched from a single bottom-hit.

  $(window).data('ajaxready', true);
  $(window).scroll(function(e){
    if (!$(window).data('ajaxready') || !fetchobjects) return;
    if ($(window).scrollTop() + $(window).height() >= $(document).height() - 300){
      console.log("Reached the bottom of the page!");
      $(window).data('ajaxready', false);
      $('#loader').fadeIn('slow', function(){
	fetchScanObjectsAjax();
      });
      $('#loader').fadeOut('slow', function(){
	$(window).data('ajaxready', true);
      });
    }
  });

  // When someone clicks a panel, turn it on / off in the browser
  // and on the backend.
 
  $('#scroll-container').on("click", ".object-frame", function(e){
    
    var h3 = $(this).find('h3').first();
    var snobjid = h3.text();
    console.log('clicked on ' + snobjid);
    var is_saved = $(this).hasClass('panel-success');
    
    console.log('starting post request for ' + snobjid);
    $.post($SCRIPT_ROOT + '/set_object_label',
           {snobjid:snobjid,
            action:'click'},
           function(){ 
             if (is_saved){
               h3.find('.pull-right').remove().fadeOut(999);
             } else {
               h3.append('<div class="pull-right">Saved <span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span></div>').fadeIn(999);
             }
       
             $(this).toggleClass('panel-default');
             $(this).toggleClass('panel-success');

           });
  });

  function isElementInViewport (el) {

    //special bonus for those using jQuery
    if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
    }
    
    var rect = el.getBoundingClientRect();
    
    return (
      rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && 
        rect.right <= (window.innerWidth || document.documentElement.clientWidth) 
    );
  }    
  function onVisibilityChange (el, callback) {
    return function () {
      /*your code here*/ 
      
      console.log('visibility ' + isElementInViewport(el));
    }
  }
  
  var handler = onVisibilityChange(el, callback);
    
  function fetchScanObjectsAjax(){
    $('.object-frame.new').toggleClass('new');
    $.getJSON($SCRIPT_ROOT + '/fetch_more',
	      function(json){
		fetchobjects  = json.has_data && ($('#toggle-autoloader').text().indexOf('off') > -1);
		var html      = json.html;
		var numnew    = json.numnew;
                
		$('#scroll-container').append(html)
                  .fadeIn(999,
                          function(){
                            $('.object-frame .new')
                              .imagesLoaded(function(){
				      var handler = onVisibilityChange($(this), function(){
					      if (!$(this).data('viewed')){
						  $(this).data('viewed', true);
						  var snobjid = $(this).find('h3').first().text();
						  $.post($SCRIPT_ROOT + '/set_object_label',
				      {snobjid:snobjid,
					      action_type:'look'},
							 function(){
							     console.log('you looked at ' + snobjid);
							 });
					      }
					  });
				      $(window).on('DOMContentLoaded load resize scroll', handler); 
				  });
			  });
	      });
  }
    });
