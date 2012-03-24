#!/usr/bin/env python
#
""" main.py
    Defined in app.yaml, by default this catches all calls to the application.
    
    The original import was this: 
    from google.appengine.ext import webapp # deleted this line
    from google.appengine.ext.webapp import util #deleted this line too
"""
import tornado.web
import tornado.wsgi
import wsgiref.handlers
"""Tornado Stuff"""

import os
import functools
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
"""Import the Jinja2 stuff"""

from docutils.core import publish_parts
import docutils.parsers.rst.directives.sourcecode
""" docutils """

import cgi
import urllib2
""" cgi for cgi.escape  for **simple** HTML escaping """

import markdown
""" Markdown """

import logging
import unicodedata
import re           # Regular Expressions!

import simplejson as json

from google.appengine.ext import db

class Project(db.Model):
    """ Project Model, duh! """
    title=db.StringProperty(required=True)
    url=db.StringProperty(required=True)
    name=db.StringProperty(required=True)                 
    description=db.StringProperty(required=True)
    date_created=db.DateTimeProperty(auto_now_add=True)
    date_updated=db.DateTimeProperty(auto_now=True)
    published=db.BooleanProperty(required=False, default=True)

class ProjectName(db.Model):
    project=db.ReferenceProperty(Project, collection_name='names',required=True)
    name=db.StringProperty(required=True)                 # 
    current=db.BooleanProperty(required=True)             # is this the current name?


# find projectName 
# Can't use a currently used name.
# If multiple projects have the same name, Tell user, which is current and which are past.
# On project page, show a permanent URI, which is a huge-ass random number/hash.
# published keeps track of deleted names. Turn this property to False to more easily "delete" entities.

# ===========================================
from google.appengine.api import users
from google.appengine.ext import db
# ===========================================

import GqlEncoder #query to json encoder

""" 
    
"""
def administrator(method):
    """Decorate with this method to restrict to site admins."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method == "GET":
                self.redirect(self.get_login_url())
                return
            raise tornado.web.HTTPError(403)
        elif not self.current_user.administrator:
            if self.request.method == "GET":
                self.redirect("/")
                return
            raise tornado.web.HTTPError(403)
        else:
            return method(self, *args, **kwargs)
    return wrapper

"""BaseHandler
    -----------
    This base handler will make a convienent place to keep methods that are accessible from all handlers that inherit from this handler class. Currently, it is empty.
"""
class BaseHandler(tornado.web.RequestHandler):
    """render_rst(self, rst)
        @self - the BaseHandler object
        @rst - the text to render into HTML
        
        http://andialbrecht.wordpress.com/2008/08/14/using-restructuredtext-on-app-engine/
        "By default, docutils tries to read configuration files from various locations. 
        But this will fail in the App Engine environment. 
    So you have to disable it by overwriting the default settings:"
    """
    def render_rst(self, rst):
        parts = publish_parts(source=rst, writer_name='html4css1',
                       settings_overrides={'_disable_config': True})
        return parts['html_body'] # changed to return 'html_body' instead of 'fragment'; 'fragment' doesn't include beginning headings unless there is a paragraph before it.



    """get_all_rst_parts(self, rst)
            @self - the BaseHandler object
            @rst - the text to render
            We are returning the entire dictionary in this one.
    """
    def get_all_rst_parts(self, rst):
        
        # in this method we are returning the entire dict
        return publish_parts(source=rst, writer_name='html4css1',
                       settings_overrides={'_disable_config': True })

    """ 
        render_md(self, md)
            self - BaseHandler
            md - raw markdown text
        
    """
    def render_md(self, md):
        
        # code modified from http://www.joeyb.org/blog/2009/06/03/django-based-blog-on-google-app-engine-tutorial-part-2
        markdown_processor = markdown.Markdown(extensions=['codehilite']) # Setup Markdown with the code highlighter
        html = markdown_processor.convert(md) # Convert the md (markdown) into html
        # to mimic the same output as Docutils, I'm wrapping the output in a classed div.
        html = '<div class="document">'+html+'</div>'
        return html
        
    """ """
    def get_request_arguments(self):
        return self.request.arguments
        
    """ """
    def make_login_link(self):
        users.create_login_url("/")
        #return "/login?continue="+self.request.uri
    
    """Implements Google Accounts authentication methods."""
    def get_current_user(self):
        # This will eventually be expanded to test for OpenID/Twitter/Facebook too.
        user = users.get_current_user()
        if user: user.administrator = users.is_current_user_admin()
        return user
        
    """ """
    def get_login_url(self, dest_url=None,federated_identity=None):
        # create_login_url(dest_url=None, _auth_domain=None, federated_identity=None)
        if dest_url==None:
            dest_url=self.request.uri
        
        if federated_identity==None:
            return users.create_login_url(dest_url=dest_url)
        else:
            return users.create_login_url(dest_url=dest_url, _auth_domain=None, federated_identity=federated_identity)
    
    """ """
    def get_logout_url(self):
        # create_logout_url(dest_url)
        return users.create_logout_url(self.request.uri)
    
    """ """
    def get_user_name(self, user):
        """ 
            If the user has filled out information use that otherwise, 
            use their email address or OpenID.
        """
        return user
    
    """ """
    # ==============================
    # Create url safe object names
    def make_safe_name(self, object_title, **kwargs):
        name = unicodedata.normalize("NFKD", u''+object_title+'').encode("ascii", "ignore")
        name = re.sub(r"(@)", " at ", name)     # converts @ -> at
        name = re.sub(r"(=)", " is ", name)     # converts = -> is
        name = re.sub(r"(&)", " and ", name)    # converts @ -> and
        name = re.sub(r"(/)", " or ", name)     # converts / -> or
        name = re.sub(r"(#)", " or ", name)     # converts # -> sharp
        name = re.sub(r" +", " ", name)         # converts multiple spaces into a single space
        name = name.strip(" ")                  # trips all spaces from beginning and end of string
        name = re.sub(r"[^\w]+"," ", name)      # convert all weird characters into spaces
        name = "-".join(name.lower().strip().split()) # convert all spaces into dashes.
        return name

    """ """
    def prepare_value_for_url(self, value, **kwargs):
        return urllib2.quote(value.encode('utf-8'))







class TemplateRendering:
    """TemplateRendering
       A simple class to hold methods for rendering templates. 
    """
    def render_template(self, template_name, variables):
        """render_template
            Returns the result of template.render to be used elsewhere. I think this will be useful to render templates to be passed into other templates.
            Gets the template directory from app settings dictionary with a fall back to "templates" as a default.
            Probably could use a default output if a template isn't found instead of throwing an exception.
        """
        template_dirs = []
        if self.settings["templates"] and self.settings["templates"] != '': 
            template_dirs.append(os.path.join(os.path.dirname(__file__),
            self.settings["templates"]))
        template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates')) # added a default for failover.
        
        env = Environment(loader = FileSystemLoader(template_dirs))
        
        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        content = template.render(variables)
        return content




        
        
        
        
        
        
class ViewProjectHandler(BaseHandler, TemplateRendering):
    def get(self, *args):
        name = args[1]
        possible_id = args[1]
        variables = {}
        user = self.get_current_user()
        variables.update({'user':user})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        variables.update({'controller':self})
        
        project=db.Query(Project).filter('name = ', name).get()
        variables.update({'name':name})
        
        logging.debug(name.isdigit())
        if project:
            variables.update({'project':project})
            name_count=project.names.count()
            variables.update({'projectnames_count': name_count})
            key = project.key()
            if key.has_id_or_name():
                variables.update({'project_id':key.id_or_name()})
            logging.debug('View Project')
            content = self.render_template('view-project.html', variables)
            self.write(content)
        else: # Project DNE - Does Not Exist
            logging.debug('Project Does Not Exist')
            if name.isdigit():
                project = Project.get_by_id(int(possible_id))
                name_count=project.names.count()
                variables.update({'projectnames_count': name_count})
                if project:
                    variables.update({'project':project})
                    variables.update({'project_id':possible_id})
                    logging.debug('View Project')
                    content = self.render_template('view-project.html', variables)
                    self.write(content)
                else:
                    content=self.render_template('404.html', variables)
                    self.write(content)
                    
            else: # not a digit
                logging.debug('Not A digit')
                project_names=db.Query(ProjectName).filter('name = ', name)
                name_count=project_names.count()
                logging.debug(name_count)
                project_names=project_names.fetch(name_count)
                if project_names and name_count == 1: # there is only one project that had that name so show it.
                    project=project_names[0].project
                    variables.update({'project':project})
                    variables.update({'project_id':project.key().id_or_name()})
                    variables.update({'projectnames_count': project.names.count()})
                    variables.update({'redirect_msg':'This URL is old. Please note the proper URL for this project is \'<a href="/view/project/'+project.name+'">/view/project/'+project.name+'</a>\' or \'<a href="/view/project/'+str(project.key().id_or_name())+'">/view/project/'+str(project.key().id_or_name())+'</a>\'.'})
                    content=self.render_template('view-project.html', variables)
                    self.write(content)
                elif project_names and name_count > 1:
                    variables.update({'projects':project_names})
                    content=self.render_template('redirect-project.html', variables)
                    self.write(content)
                else:
                    content=self.render_template('404.html', variables)
                    self.write(content)





# ADD Project
# Needs BOTH GET and POST

class AddProjectHandler(BaseHandler, TemplateRendering):
    #GET posts to the POST below
    @administrator
    def get(self, *args):
        logging.debug('GET AddProjectHandler')
        variables = {}
        user = self.get_current_user()
        variables.update({'user':user})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        variables.update({'controller':self})
        
        logging.info('GET add-project.html -- ')
        content = self.render_template('add-project.html', variables)
        self.write(content)

    # GET posts to this POST
    @administrator
    def post(self, *args):
        logging.debug('POST AddProjectHandler')
        variables = {}
        
        error = {}
        # get values
        user = self.get_current_user()
        title = self.get_argument('title','')   
        url = self.get_argument('url','')
        name = self.make_safe_name(title)   # make name
        description = self.get_argument('description','')
        
        project_exists=db.Query(Project).filter('name = ', name).get()
        
        if title == '':
            logging.debug('title is empty')
            error.update({'title':'The title cannot be empty.'})
        else:
            if project_exists:
                logging.debug('title already in use.')
                error.update({'title':'Title, \''+title+'\', is in use by another project.'})
            
        if url == '':
            logging.debug('url is empty')
            error.update({'url':'The url cannot be empty.'})
            
        if description == '':
            logging.debug('description is empty')
            error.update({'description':'The description cannot be empty.'})
        
        variables.update({'controller':self})
        variables.update({'user':user})
        variables.update({'title':title})
        variables.update({'name':name})
        variables.update({'url':url})
        variables.update({'description':description})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        
        if error: 
            logging.debug(error)
            variables.update({'error':error})
            logging.info('GET add-project.html -- ')
            content = self.render_template('add-project.html', variables)
            self.write(content)
        else:
            #project_exists=db.Query(Project).filter('name = ', name).get()
            logging.debug(project_exists)
            if not project_exists: # if there is not already a project with that title/name
                new_project=Project(
                    title=title,
                    name=name,
                    url=url,
                    description=description
                )
                new_project.put()
                ProjectName(project=new_project,
                            name=name,
                            current = True,
                            published=True).put()
                            
                if new_project.key():
                    logging.debug('project now exists')
                    logging.info('REDIRECT - /view/project/'+new_project.name+'')
                    self.redirect('/view/project/'+new_project.name+'')
                else:
                    logging.debug("new_project PUT Unsuccessful")
                    logging.info('GET add-project.html -- ')
                    content = self.render_template('add-project.html', variables)
                    self.write(content)
            else:
                logging.debug('project "'+ name +'", already exists.')
                error_message = {}
                error_message.update({'msg':'Name already taken'})
                variables.update({'error_msg': error_message})
                variables.update({'project':project_exists})
                
                logging.info('GET add-project.html -- ')
                content = self.render_template('add-project.html', variables)
                self.write(content)










class RootHandler(BaseHandler, TemplateRendering):
    def get(self, *args):        
        logging.debug('RootHandler:GET')
        variables = {}
        query = Project.all()
        query.order('-date_updated')
        projects = query.fetch(12)
        
        user = self.get_current_user()
        variables.update({'user':user})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        variables.update({'controller':self})
        
        variables.update({'projects':projects})
        logging.info('GET index.html -- ')
        
        message=self.get_argument('m',None)
        if message:
            message=urllib2.unquote(message)
            variables.update({'msg': message})
            
        err_msg=self.get_argument('e',None)
        if err_msg:
            err_msg=urllib2.unquote(err_msg)
            variables.update({'err_msg': err_msg})

        content = self.render_template('index.html', variables)
        self.write(content)
        
        
        
        
        
        
        
class ListProjectsHandler(BaseHandler, TemplateRendering):
    def get(self, *args):
        logging.debug('ListProjectsHandler:GET')
        variables = {}
        query = Project.all()
        query.order('-date_updated')
        projects = query.fetch(12)
        
        user = self.get_current_user()
        variables.update({'user':user})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        variables.update({'controller':self})
        
        variables.update({'projects':projects})
        logging.info('GET index.html -- ')
        content = self.render_template('index.html', variables)
        self.write(content)
        
        





class UpdateProjectHandler(BaseHandler, TemplateRendering):
    @administrator
    def get(self, *args):
        logging.debug('GET UpdateProjectHandler')
        variables = {}
        variables.update({'user':self.get_current_user()})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        variables.update({'controller':self})
        
        project=db.Query(Project).filter('name = ', args[1]).get()
        variables.update({'name':args[1]})
        if project:
            variables.update({'project':project})
            key = project.key()
            if key.has_id_or_name():
                variables.update({'project_id':key.id_or_name()})
            else:
                variables.update({'project_id':-1})
            
            # ERROR if project_id=-1
            
            content = self.render_template('update-project.html', variables)
            self.write(content)
        else: # Project DNE - Does Not Exist
            content = self.render_template('404.html', variables)
            self.write(content)

    # GET posts to this POST
    @administrator
    def post(self, *args):
        logging.debug('POST AddProjectHandler')
        variables = {}
        error = {}
        variables.update({'controller':self})
        
        # NEW PROJECT VALUES
        user = self.get_current_user()
        title = self.get_argument('title','')   # (arg_name, default)
        url = self.get_argument('url','')
        name = self.make_safe_name(title)
        description = self.get_argument('description','')
        project_id = self.get_argument('project-id', -1) # can't actually be empty
        
        # OLD PROJECT VALUES
        old_title = self.get_argument('old-title','')
        old_url = self.get_argument('old-url','')
        old_name = self.make_safe_name(old_title)
        old_description = self.get_argument('old-description','')
        old_project_id = self.get_argument('project-id', -1) # can't actually be empty
        
        # PASS ALL PROJECT VALUES (OLD & NEW) to template
        variables.update({'user':user})
        variables.update({'title':title})
        variables.update({'name':name})
        variables.update({'url':url})
        variables.update({'description':description})
        variables.update({'old-title':old_title})
        variables.update({'old-url':old_url})
        variables.update({'old-description':old_description})
        
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        
        # GET THE PROJECT
        project=Project.get_by_id(int(project_id))
        logging.debug(project)
        # IF PROJECT NOT FOUND (project == NONE) BY ID
        if not project:
            # find project by name
            project=db.Query(Project).filter('name = ', args[1]).get()
        if not project:
            #error
            content = self.render_template('404.html', variables)
            self.write(content)
            
            
        logging.debug(project_id)
        logging.debug(project)
        
        # get projectNames
        projectname_by_new_name=db.Query(ProjectName).filter('name = ', name).filter('current = ', True).get()
        if title == '':
            logging.debug('title is empty')
            error.update({'title':'The title cannot be empty.'})
        elif title != old_title or name != old_name:
            # changing title or name
            logging.debug('Title or Name of Project has changed.')
            if projectname_by_new_name and projectname_by_new_name.project != project:
                logging.debug('new name is in current use') # check ProjectName(s)
                error.update({'title':'The title is currently in use by another project.'})
        if url == '':
            logging.debug('url is empty')
            error.update({'url':'The url cannot be empty.'})
        #elif is_valid_url(url): # now, check if value is a URL or not.
        #    pass
        #URL is OK
        
        if description == '':
            logging.debug('description is empty')
            error.update({'description':'The description cannot be empty.'})
        else:#DESCRIPTION is OK
            pass
            
        if error: 
            logging.debug(error)
            logging.debug(project)
            variables.update({'error':error})
            variables.update({'project':project})
            logging.info('GET update-project.html -- ')
            content = self.render_template('update-project.html', variables)
            self.write(content)
            
        else:
            logging.debug('NO EASY ERRORS')
            project.title = title
            project.name = name
            project.url = url
            project.description = description
            project.put()
            # make into a method
            #old_project_name = ProjectName.all().filter('project_id', int(project_id)).filter('current', True).get()
            old_projectname=project.names.filter('current=',True).get()
            if old_projectname:
                old_projectname.current = False
                old_projectname.put()
            
            projectname_used_previously=project.names.filter('name = ', name).get()
            
            logging.debug(projectname_used_previously)
            logging.debug('name='+name)
            if projectname_used_previously:
                projectname_used_previously.current = True
                projectname_used_previously.put()
            else:
                logging.debug('Make new Project Name')
                new_projectname = ProjectName(name = name, current = True, project = project)
                new_projectname.put()
                
            logging.info('REDIRECT - /view/project/'+ name +'')            # REDIRECT
            self.redirect('/view/project/'+ name +'')







class Embedded_ViewProjectsListHandler(BaseHandler, TemplateRendering): 
    def get(self, *args):
        max_projects = 20
        min_projects = 1
        type = self.get_argument('t','html') # type of data to return
        id = int(self.get_argument('id', 0)) 
        # set min if no value is given
        count = int(self.get_argument('c',min_projects)) # give a default
        if count > max_projects:    # prevent user from asking too much
            count = max_projects
        elif count < min_projects:  # prevent user from asking too little
            count = min_projects
        
        variables = {}
        projects_query=Project.all()
        projects = projects_query.fetch(count)
        filtered_projects = []
        for project in projects: #filter out the current project in the list
            key = project.key()
            if key.has_id_or_name() and int(key.id_or_name()) != id:
                filtered_projects.append(project)
        variables.update({'projects': filtered_projects})
        
        # HTML
        content = self.render_template('embedded_viewProjectsList.html', variables)
        if format == 'json':
            self.set_header("Content-Type", "application/json")
        else:
            self.set_header("Content-Type", "text/html")
        self.write(content)








class Embedded_ViewProjectsGridHandler(BaseHandler, TemplateRendering): 
    def get(self, *args):
        max_projects = 20
        min_projects = 1
        type = self.get_argument('t','html') # type of data to return
        id = int(self.get_argument('id', 0))
        # set min if no value is given
        count = int(self.get_argument('c',min_projects)) # give a default
        if count > max_projects:    # prevent user from asking too much
            count = max_projects
        elif count < min_projects:  # prevent user from asking too little
            count = min_projects

        variables = {}
        projects_query=Project.all()
        projects = projects_query.fetch(count)
        logging.debug(projects)
        filtered_projects = []
        for project in projects: #filter out the current project in the list
            key = project.key()
            if key.has_id_or_name() and int(key.id_or_name()) != id:
                filtered_projects.append(project)
        variables.update({'projects': filtered_projects})

        # HTML
        content = self.render_template('embedded_viewProjectsGrid.html', variables)
        
        # JSON test
        #content=json.JSONEncoder().encode({"foo": ["bar", "baz"]})
        
        if format == 'json':
            self.set_header("Content-Type", "application/json")
        else:
            self.set_header("Content-Type", "text/html")
        self.write(content)







class Rest_GetProjectsHandler(BaseHandler, TemplateRendering):
    def get(self, *args):
        max_projects = 20
        min_projects = 1
        format = self.get_argument('f','json') # type of data to return (html|json)
        id = int(self.get_argument('id', 0))
        count = int(self.get_argument('c',min_projects)) # min_project is the default
        callback_name=self.get_argument('callback','__jqjsp')
        
        # set min if no value is given
        count = int(self.get_argument('c',min_projects)) # give a default
        
        if count > max_projects:    # prevent user from asking too much
            count = max_projects
        elif count < min_projects:  # prevent user from asking too little
            count = min_projects
        # ======================================
        projects_query=Project.all().order('-date_created')
        projects=projects_query.fetch(count)
        variables={}
        filtered_projects = []
        for project in projects: #filter out the current project in the list
            key = project.key()
            if key.has_id_or_name() and int(key.id_or_name()) != id:
                filtered_projects.append(project)
        variables.update({'projects': filtered_projects})
        
        if format == 'json':
            content=GqlEncoder.encode(filtered_projects)
            self.set_header("Content-Type", "application/json")
            self.write(callback_name+'({projects:' + content + '})')
        else:   # Not tested
            content = self.render_template('rest_getProjectsHandler.html', variables)
            self.set_header("Content-Type", "text/html")







class DeleteProjectHandler(BaseHandler, TemplateRendering):
    """
        GET
    """
    def get(self, *args):
        logging.debug('GET DeleteProjectHandler')
        variables = {}
        user = self.get_current_user()
        variables.update({'user':user})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        variables.update({'controller':self})
        project_id = self.get_argument('project-id', -1) # can't actually be empty
        project_to_delete = self.get_argument('delete', -1) # can't actually be empty
        project=Project.get_by_id(int(project_id)) # find by id
        
        logging.debug(project)
        if not project:
            project=db.Query(Project).filter('name = ', args[1]).get() #find by name
            if not project:
                #error
                content = self.render_template('404.html', variables)
                self.write(content)

        logging.debug(project)
        variables.update({'name':args[1]})
        if project:
            variables.update({'project':project})
            key = project.key()
            if key.has_id_or_name():
                variables.update({'project_id':key.id_or_name()})
                logging.debug(key.id_or_name())
            else:
                variables.update({'project_id':-1})
                logging.debug('-1')
            content = self.render_template('delete-project.html', variables)
            self.write(content)
        else: # Project DNE - Does Not Exist
            content = self.render_template('404.html', variables)
            self.write(content)



    """
        
    """
    def post(self, *args):
        logging.debug('POST DeleteProjectHandler')
        variables = {}
        user = self.get_current_user()
        variables.update({'user':user})
        variables.update({'logout':users.create_logout_url(self.request.uri)})
        variables.update({'login': users.create_login_url(self.request.uri)})
        variables.update({'controller':self})
        
        project_name = args[1]
        delete_project = self.get_argument('delete',-1)
        cancel_delete = self.get_argument('cancel',-1)
        project_id = self.get_argument('project-id',-1)
        logging.debug(cancel_delete)
        
        if cancel_delete and int(cancel_delete) != -1:
            self.redirect('/?m='+self.prepare_value_for_url("Delete Canceled.")+'')
        elif delete_project and int(delete_project) == -1:
            self.redirect('/delete/project/'+project_name+'?e='+self.prepare_value_for_url("Project Not Deleted; You must click the checkbox below to confirm you want to delete.")+'')
        else:
            if delete_project and project_id and int(project_id) != int(delete_project):
                self.redirect('/?e='+self.prepare_value_for_url("Project Not Deleted. Keys and Name did not match the same project.")+'')
            else:
                project=Project.get_by_id(int(project_id)) # find by id
                if not project: # if project not found by id
                    project=db.Query(Project).filter('name = ', args[1]).get() #find by name
                    
                if project:
                    project_key = project.key()
                    if project_key.has_id_or_name():
                        project_key_id=project_key.id_or_name()
                        logging.debug('project_key_id:' + str(project_key_id))
                        logging.debug('delete_project:' + str(delete_project))
                        logging.debug('project_id:' + str(project_id))
                        variables.update({'name':args[1]})
                        if int(project_key_id) == int(delete_project) and int(delete_project) == int(project_id):
                            logging.info('Redirect: /~') # REDIRECT
                            # delete project
                            logging.debug('Delete Project')
                            project.delete()
                            # also need to delete ProjectNames
                            logging.debug('Delete ProjectNames')
                            for projectname in project.names:
                                projectname.delete()
                            # REDIRECT
                            self.redirect('/?m=Project%20'+self.prepare_value_for_url(project.title)+'%20deleted.')
                        else: 
                            self.redirect('/?e='+self.prepare_value_for_url("Project Not Deleted. Keys and Name did not match the same project.")+'')
                    else: 
                        self.redirect('/?e='+self.prepare_value_for_url("ERROR: No KEY or ID")+'')
                else: 
                    self.redirect('/?e='+self.prepare_value_for_url("Could Not Delete Project: Project Not Found.")+'')






"""
settings dictionary
The settings dictionary stores, of all things, settings, for the application. It's no joke! You can include your own entries such as the name of the application as you want it to be on the top of each page ("page_title" above) or tell Tornado to turn on or off the xsrf_cookies (among other things).
Using self.settings["page_title"] we can access the page_title entry of the settings dictionary from within your handlers.
"""
settings = {
    "page_title": u"App Gallery",
    "templates": "views",
    "sourcecode_stylesheet": "default",
    "xsrf_cookies": False,
}





"""The Main Function, not to be confused with the MainHandler.
This is the webapp version:
    application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
This is the tornado version:
    application = tornado.wsgi.WSGIApplication([ (r"/", MainHandler), ], **settings) 
We also have to run it differently too:
    wsgiref.handlers.CGIHandler().run(application)
"""
def main():
    logging.getLogger().setLevel(logging.DEBUG) # Turn on logging
    application = tornado.wsgi.WSGIApplication([ 
        (r"(/)", RootHandler),
        (r"(/add/project/?)", AddProjectHandler),               # GET&POST
        (r"(/delete/project/([^/]+)/?)", DeleteProjectHandler),         # POST
        (r"(/edit/project/([^/]+)/?)", UpdateProjectHandler),   # GET
        (r"(/update/project/?)", UpdateProjectHandler),         # POST/UPDATE
        (r"(/view/project/([^/]+)/?)", ViewProjectHandler),     # GET
        
        # The Peoples' Handlers - Just to help people out.
        (r"(/view/projects?/?)", ListProjectsHandler),     # GET
        (r"(/projects?/?)", ListProjectsHandler),     # GET
        
        (r"(/api/v1/embed/view/projects/list/?)", Embedded_ViewProjectsListHandler),     # GET - /view/projects/list/?c=10&p=1
        (r"(/api/v1/embed/view/projects/grid/?)", Embedded_ViewProjectsGridHandler),     # GET 
        
        (r"(/api/v1/ajax/view/projects/list/?)", Rest_GetProjectsHandler),     # GET ?f=format values: (html|json)

        ], **settings)
    """ Set up a tornado WSGIApplication """
    
    # We have to run it differently too:
    wsgiref.handlers.CGIHandler().run(application)
    """ Use the wsgiref in the Python standard library to run the Tornado application. """



if __name__ == '__main__':
    main()
