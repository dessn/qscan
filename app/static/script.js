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
	    
	    //var snobjid = $(this).find('.panel-title').first().text();	

	    var h3 = $(this).find('h3').first();
	    var is_saved = $(this).hasClass('panel-success');
	    
	    if (is_saved){
		h3.find('.pull-right').remove().fadeOut(999);
	    } else {
		h3.append('<div class="pull-right">Saved <span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span></div>').fadeIn(999);
	    }

	    $(this).toggleClass('panel-default');
	    $(this).toggleClass('panel-success');
	});
	
    $('#submit-button').data('ajaxready', true).click(function(e){
	    if (!$('#submit-button').data('ajaxready')) return;	     
	    var badge = $(this).children().first();
	    var numtot = parseInt(badge.text(), 10);
	    if (numtot == 0) return;
	    else {
		var saves = $(document).find('.object-frame.panel-success');
		var junk  = $(document).find('.object-frame.panel-default');
		var save_snobjids = jQuery.map(saves,
					       function(element){
						   return parseInt(jQuery(element).find('h3').first().text().replace('Saved', ''));
					       });
		var junk_snobjids = jQuery.map(junk,
					       function(element){
						   return parseInt(jQuery(element).find('h3').first().text());
					       });
		
		$('#loader').fadeIn('slow', function(){
			$('#submit-button').data('ajaxready', false);

			console.log('save snobjids: ' + save_snobjids);
			console.log('junk_snobjids: ' + junk_snobjids);

			$.post($SCRIPT_ROOT + '/register_scan',
			       {"save_snobjids":save_snobjids,
				       "junk_snobjids":junk_snobjids},
			       function(){
				   $(document).find('.object-frame').remove();
				   $('#submit-badge').text("0");
				   fetchScanObjectsAjax();
				   $('#submit-button').data('ajaxready', true);
				   $('#loader').fadeOut('slow');
			       }
			       );
		    });
	    }
	});

    function fetchScanObjectsAjax(){
	$.getJSON($SCRIPT_ROOT + '/fetch_more',
		  function(json){
		      fetchobjects  = json.has_data;
		      var html      = json.html;
		      var numnew    = json.numnew;
		      
		      $('#scroll-container').append(html).fadeIn(999);
		      
		      // Update the submit button badge so that the
		      // number of viewport-candidates is displayed.

		      var badgenum = parseInt($('#submit-badge').text(),
					      10);
		      
		      $('#submit-badge').text(badgenum + numnew);
		  });
    }
    
    });
