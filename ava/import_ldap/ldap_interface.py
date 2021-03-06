import os

__author__ = 'ladynerd'

from ldap3 import Server, Connection, LDAPExceptionError, SUBTREE
import sys
import json


class ActiveDirectoryHelper:
    def __init__(self):
        pass

    PAGESIZE = 1000

    def get_connection(self, parameters):
        try:
            server = Server(parameters.server)
            ldap_conn = Connection(server, user=parameters.user_dn, password=parameters.user_pw,
                                   auto_bind=True)
            return ldap_conn

        except LDAPExceptionError as e:
            print(e.message)
            print(e.args)
            sys.exit(1)

    def search(self, parameters, filterby, attrs):

        # bind to the LDAP server using the credentials provided
        connection = self.get_connection(parameters)

        connection.search(search_base=parameters.dump_dn, search_filter=filterby, search_scope=SUBTREE,
                          attributes=attrs, paged_size=5)

        # store the search results
        results = connection.response

        # extract the cookie from the search result to allow for paged session continuation
        cookie = connection.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']

        # while the results contain a cookie (ie. more records left to retrieve)
        while cookie:

            # search again using the cookie to continue paging
            connection.search(search_base=parameters.dump_dn, search_filter=filterby, search_scope=SUBTREE,
                              attributes=attrs, paged_size=5, paged_cookie=cookie)

            # append the search results
            results += connection.response

            # get the cookie again
            cookie = connection.result['controls']['1.2.840.113556.1.4.319']['value']['cookie']

        # export the combined paged results to json format
        results_json = connection.response_to_json(search_result=results)

        # Feature and testing toggle to allow developers to test export new test data from LDAP server
        # Uses an environment variable to decide whether to dump the data to file or not
        # To toggle this feature on, ensure that the environment variable 'CREATE_MOCK_LDAP' is set
        if os.environ.get('CREATE_MOCK_LDAP'):
            if 'user' in filterby:
                prefix = 'user'
            else:
                prefix = 'group'
            self.export_ldap_json(prefix, results_json)

        # end of toggled feature

        return results_json

    # Exports a JSON string to a file
    @staticmethod
    def export_ldap_json(prefix, results_json):
        filename = 'ava/testdata/ldap_' + prefix + '_data.json'

        with open(filename, 'w') as outfile:
            json.dump(results_json, outfile)
        outfile.close()

    # imports the users from an LDAP instance
    @staticmethod
    def import_users(parameters):
        # Feature and testing toggle to allow developers to test LDAP import without having
        # and LDAP VM or infrastructure at hand
        # Uses an environment variable to decide whether to test against local JSON file or actual
        # LDAP server instance
        # To test locally, ensure that the environment variable 'USE_MOCK_LDAP' is set

        if os.environ.get('USE_MOCK_LDAP'):
            with open("ava/testdata/ldap_user_data.json", 'r') as infile:
                results = json.load(infile)
            infile.close()
            return results

        else:
            # specify that we only care about users
            filter_fields = '(objectclass=user)'

            # specify the fields to bring back for this user
            attributes = ['distinguishedName', 'objectGUID', 'objectSid', 'cn', 'accountExpires', 'adminCount',
                          'badPasswordTime', 'badPwdCount', 'description', 'displayName', 'isCriticalSystemObject',
                          'lastLogoff', 'lastLogon', 'lastLogonTimestamp', 'logonCount', 'lockoutTime', 'name',
                          'primaryGroupID', 'pwdLastSet', 'sAMAccountName', 'sAMAccountType', 'uSNChanged',
                          'uSNCreated', 'userAccountControl', 'whenChanged', 'whenCreated', 'memberOf',
                          'proxyAddresses']

            # return a search result for these filter_fields and attributes in JSON format
            ad_helper = ActiveDirectoryHelper()
            return ad_helper.search(parameters, filter_fields, attributes)

    # imports the groups from an LDAP instance
    @staticmethod
    def import_groups(parameters):
        # Feature and testing toggle to allow developers to test LDAP import without having
        # and LDAP VM or infrastructure at hand
        # Uses an environment variable to decide whether to test against local JSON file or actual
        # LDAP server instance
        # To test locally, ensure that the environment variable 'USE_MOCK_LDAP' is set

        if os.environ.get('USE_MOCK_LDAP'):
            with open("ava/testdata/ldap_group_data.json", 'r') as infile:
                results = json.load(infile)
            infile.close()
            return results

        else:
            # specify that we only care about groups
            filter_fields = '(objectclass=group)'

            # specify the fields to bring back for this group
            attributes = ['distinguishedName', 'objectGUID', 'objectSid', 'cn', 'name', 'objectCategory',
                          'sAMAccountName']

            # return a search result for these filter_fields and attributes in JSON format
            ad_helper = ActiveDirectoryHelper()
            return ad_helper.search(parameters, filter_fields, attributes)
