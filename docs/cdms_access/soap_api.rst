.. _SOAP_API:

SOAP API
--------

Instead of simulating the login process and obtain the cookie, the SOAP API go through the steps needed in order
to obtain the token from the ID Provider/RSTS in SOAP.

The library `cdms_api.soap.api` does this for you but it's basic and only has a few methods implemented at the moment.

Useful links:

  - `WIF, ADFS 2 and WCF–Part 6: Chaining multiple Token Services <https://leastprivilege.com/2010/10/28/wif-adfs-2-and-wcfpart-6-chaining-multiple-token-services/>`_

In C#
.....

Unsurprisingly, it's easier to connecto to CDMS in C# by using the Microsoft SDK than to do it manually.

A very ugly but working C# script that can be used to test the connection can be found below. You can use it in
VisualStudio on Windows and MITM the requests/responses to check how the SOAP XML should be structured and
do the same in python.


.. code:: python

    using System;
    using System.IdentityModel.Protocols.WSTrust;
    using System.IdentityModel.Tokens;
    using System.Net;
    using System.ServiceModel;
    using System.ServiceModel.Security;
    using WSTrustChannelFactory = Microsoft.IdentityModel.Protocols.WSTrust.WSTrustChannelFactory;
    using RequestSecurityToken = Microsoft.IdentityModel.Protocols.WSTrust.RequestSecurityToken;
    using IWSTrustChannelContract = Microsoft.IdentityModel.Protocols.WSTrust.IWSTrustChannelContract;
    using WSTrust13Constants = Microsoft.IdentityModel.Protocols.WSTrust.WSTrust13Constants;
    using UserNameWSTrustBinding = Microsoft.IdentityModel.Protocols.WSTrust.Bindings.UserNameWSTrustBinding;
    using Microsoft.IdentityModel.Protocols.WSTrust.Bindings;
    using Microsoft.Xrm.Sdk.Client;
    using Microsoft.Xrm.Sdk;
    using Microsoft.Xrm.Sdk.Query;
    using System.ServiceModel.Description;
    using System.ServiceModel.Configuration;
    using System.ServiceModel.Web;

    public class DynamicsRequests
    {

        public static SecurityToken GetToken(string username, string password, string endpointUri, string realm)
        {
            // use WSTrust and SSL Transport Mode with security credentials being sent with the message.
            var endpoint = new EndpointAddress(endpointUri);
            var binding = new UserNameWSTrustBinding(SecurityMode.TransportWithMessageCredential);
            var factory = new WSTrustChannelFactory(binding, endpoint);
            factory.TrustVersion = TrustVersion.WSTrust13;

            factory.Credentials.UserName.UserName = username;
            factory.Credentials.UserName.Password = password;
            factory.Credentials.SupportInteractive = false;

            // Symmetric key request.
            var rst = new RequestSecurityToken
            {
                RequestType = RequestTypes.Issue,
                AppliesTo = new EndpointAddress(realm),
                KeyType = KeyTypes.Symmetric
            };

            // Token will be encrypted with ADFS Token Signing cert.
            var channel = factory.CreateChannel();
            return channel.Issue(rst);
        }

        private static SecurityToken GetRSTSToken(SecurityToken idpToken, string endpointUri, string realm)
        {
            var binding = new IssuedTokenWSTrustBinding();
            binding.SecurityMode = SecurityMode.TransportWithMessageCredential;

            var factory = new WSTrustChannelFactory(
                binding,
                endpointUri);
            factory.TrustVersion = TrustVersion.WSTrust13;
            factory.Credentials.SupportInteractive = false;

            var rst = new RequestSecurityToken
            {
                RequestType = RequestTypes.Issue,
                AppliesTo = new EndpointAddress(realm),
                KeyType = KeyTypes.Symmetric
            };

            var channel = factory.CreateChannelWithIssuedToken(idpToken);
            return channel.Issue(rst);
        }

        public static IOrganizationService GetOrganizationService(SecurityToken token)
        {
            var binding = new WS2007FederationHttpBinding(WSFederationHttpSecurityMode.TransportWithMessageCredential);
            binding.Security.Message.EstablishSecurityContext = false;
            binding.Security.Message.IssuedKeyType = SecurityKeyType.SymmetricKey;
            binding.Security.Message.NegotiateServiceCredential = false;

            ChannelFactory<IOrganizationService> factory = new ChannelFactory<IOrganizationService>(binding, "https://<crm-url>/XRMServices/2011/Organization.svc");
            factory.Credentials.SupportInteractive = false;

            return factory.CreateChannelWithIssuedToken(token);
        }

        public static void MakeQuery(SecurityToken token)
        {
            IOrganizationService service = GetOrganizationService(token);

            QueryExpression query = new QueryExpression
            {
                EntityName = "account",
                ColumnSet = new ColumnSet("name", "address1_city", "emailaddress1"),
                TopCount = 2
            };
            EntityCollection orgs = service.RetrieveMultiple(query);

            foreach (var c in orgs.Entities)
            {
                System.Console.WriteLine("Name: " + c.Attributes["name"]);

                if (c.Attributes.Contains("address1_city"))
                    System.Console.WriteLine("Address: " + c.Attributes["address1_city"]);

                if (c.Attributes.Contains("emailaddress1"))
                    System.Console.WriteLine("E-mail: " + c.Attributes["emailaddress1"]);
            }
        }



        static public void Main()
        {
            var crmUrl = "...";
            var ssoSimpleUrl = "...";
            var ssoUrl = "...";
            var adfsUrl = "...";
            var username = "...";
            var password = "...";

            var idpToken = GetToken(username, password, adfsUrl, ssoSimpleUrl);
            var token = GetRSTSToken(idpToken, ssoUrl, crmUrl);

            System.Console.WriteLine(token);
            MakeQuery(token);
        }
    }
