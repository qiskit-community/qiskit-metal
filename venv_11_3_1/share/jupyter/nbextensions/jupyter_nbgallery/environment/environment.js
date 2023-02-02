$.ajaxSetup({ xhrFields: { withCredentials: true } });

define(['jquery', 'base/js/utils', 'base/js/dialog', 'services/config'], function($, utils, dialog, configmod) {

    // Save preferences pulled from nbgallery
    function set_preferences(common_config, notebook_config, response) {
        if(response['smart_indent'] != null) {
            notebook_config.update({
                CodeCell:{
                    cm_config:{smartIndent:response['smart_indent']}
                }
            });
        }
        if(response['auto_close_brackets'] != null) {
            notebook_config.update({
                CodeCell:{
                    cm_config:{autoCloseBrackets:response['auto_close_brackets']}
                }
            });
        }
        if(response['indent_unit'] != null) {
            notebook_config.update({
                CodeCell:{
                    cm_config:{indentUnit:response['indent_unit']}
                }
            });
            notebook_config.update({
                CodeCell:{
                    cm_config:{tabSize:response['indent_unit']}
                }
            });
        }        
        if(response['easy_buttons'] != null) {
            common_config.update({
                nbgallery:{easy_buttons:response['easy_buttons']}
            });
        }
    }

    // Download and re-apply preferences stored in nbgallery
    function download_preferences(common_config, notebook_config) {
        console.log('Fetching Jupyter preferences from nbgallery');
        $.ajax({
            method: 'GET',
            headers: {Accept: 'application/json'},
            url: common_config.data.nbgallery.url + '/preferences',
            success: function(response) {
                set_preferences(common_config, notebook_config, response);
            }
        });
    }

   // Register this Juypter environment at nbgallery
   function register_environment(common_config, base_url) {
        console.log('Registering Jupyter environment at nbgallery');
        $.ajax({
            method: 'POST',
            headers: {'Accept' : 'application/json'},
            url: common_config.data.nbgallery.url + '/environments',
            data: {
                name: common_config.data.nbgallery.client.name,
                url: window.location.origin + base_url
            },
            xhrFields: {withCredentials: true},
            success: function(data) {
                common_config.update({nbgallery: {environment_registered: true}});
            },
        });
    }

    function load_ipython_extension() {
        var base_url = utils.get_body_data('baseUrl');
        var common_config = new configmod.ConfigSection('common', {base_url: base_url});
        var notebook_config = new configmod.ConfigSection('notebook', {base_url: base_url})
        common_config.load();
        notebook_config.load();
        common_config.loaded.then(function() {
            notebook_config.loaded.then(function() {
                if(common_config.data.nbgallery.environment_registered) {
                    // Don't keep registering with nbgallery repeatedly
                    return;
                }
                register_environment(common_config, base_url);
                download_preferences(common_config, notebook_config);
            });
        });
    }

    return {load_ipython_extension : load_ipython_extension};
});
