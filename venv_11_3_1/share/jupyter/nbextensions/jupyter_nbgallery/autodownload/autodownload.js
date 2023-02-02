$.ajaxSetup({ xhrFields: { withCredentials: true } });

define([
  'jquery',
  'base/js/utils',
  'services/config',
  'base/js/events'
], function(
  $,
  utils,
  configmod,
  events
) {
  var upload_notebook = function(folder, name, notebook) {
    // this SHOULD be a PUT to api/contents/NotebookName.ipynb, but since FireFox won't
    // PKI-enable an OPTIONS request, and an OPTIONS request is necessary on PUTs, we 
    // have a server-side extension that proxies the PUT through a POST. 
    $.ajax({
      url: utils.get_body_data('baseUrl') + 'post/' + folder + '/' + encodeURIComponent(name) + '.ipynb',
      type: 'POST',
      success: function() { 
        console.log('Successfully downloaded ' + name);
      },
      error: function(response) {
        console.log('Failed upload: ' + name);
        console.log(response);
      },
      data: JSON.stringify({
        type: 'notebook',
        content: JSON.parse(notebook)
      })
    });
  }
  
  var fetch_notebook = function(url, folder, name) {
    $.ajax({
      method: 'GET',
      headers: { Accept: 'application/json' },
      url: url,
      cache: false,
      success: function(notebook) { 
        upload_notebook(folder, name, notebook);
      }
    });
  }
  
  var download_notebooks = function(folder, base, endpoint) {
    $.ajax({
      method: 'GET',
      url: utils.get_body_data('baseUrl') + 'api/contents/' + encodeURIComponent(folder),
      cache: false,
      success: function(response) { 
        // Folder already exists - do nothing
      },
      error: function(response){
        // Folder doesn't exist - download notebooks from gallery
        console.log('Downloading notebooks to ' + folder);
        $.ajax({
          method: 'POST',
          url: utils.get_body_data('baseUrl') + 'post/' + encodeURIComponent(folder) + '',
          data: JSON.stringify({ type: 'directory' }),
          cache: false,
          success: function(response) { 
            Jupyter.notebook_list.load_list(); // refresh to show new directory
            $.ajax({
              method: 'GET',
              headers: { Accept: 'application/json' },
              url: base + endpoint,
              cache: false,
              success: function(response) { 
                for (i in response) {
                  var metadata = response[i];
                  var url = base + '/notebooks/' + metadata.uuid + '/download?clickstream=false';
                  fetch_notebook(url, folder, metadata.title.replace(/\//g,'∕'));
                }
              }
            });
          }
        });
      }
    });
  }

  function load_ipython_extension() {
    var config = new configmod.ConfigSection('common', {base_url: utils.get_body_data('baseUrl')});
    config.load();
  
    // Post the client name/url to the gallery as an environment
    config.loaded.then(function() {
      var nbgallery = config['data'].nbgallery;
      var base = nbgallery.url;
  
      download_notebooks('Starred', base, '/notebooks/stars');
      download_notebooks('Recently Executed', base, '/notebooks/recently_executed');
  
      console.log('gallery-autodownload loaded');
  
      $.ajax({
        method: 'GET',
        headers:{
          Accept: 'application/json'
        },
        url: base + '/preferences',
        success: function(response){
          var notebookConfig = new configmod.ConfigSection('notebook', {base_url: utils.get_body_data('baseUrl')});
          notebookConfig.load();
          notebookConfig.loaded.then(function(){
            if(response['smart_indent'] != null ){
              notebookConfig.update({CodeCell:{cm_config:{smartIndent:response['smart_indent']}}});
            }
            if(response['auto_close_brackets'] != null ){
              notebookConfig.update({CodeCell:{cm_config:{autoCloseBrackets:response['auto_close_brackets']}}});
            }
            if(response['indent_unit'] != null ){
              notebookConfig.update({CodeCell:{cm_config:{indentUnit:response['indent_unit']}}});
              notebookConfig.update({CodeCell:{cm_config:{tabSize:response['indent_unit']}}});
            }        
          })
          
          var config = new configmod.ConfigSection('common', {base_url: utils.get_body_data('baseUrl')});
          config.load();
          config.loaded.then(function() {
            if(response['easy_buttons'] != null ){
              config.update({nbgallery:{easy_buttons:response['easy_buttons']}});
            }
          })
    
          var config = new configmod.ConfigSection('common', {base_url: utils.get_body_data('baseUrl')});
          config.load();
          config.loaded.then(function() {
            if(response['easy_buttons'] != null ){
              config.update({nbgallery:{easy_buttons:response['easy_buttons']}});
            }
          });
        }
      });
    });
  }
  return {load_ipython_extension : load_ipython_extension};
});


