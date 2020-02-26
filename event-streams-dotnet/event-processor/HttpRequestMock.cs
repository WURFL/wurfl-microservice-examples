using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;

namespace event_processor
{
    internal class HttpRequestMock : HttpRequest
    {
        private IHeaderDictionary _headers;
        
        public HttpRequestMock()
        {
            _headers = new HeaderDictionary();
        }

        public override HttpContext HttpContext => throw new System.NotImplementedException();

        public override string Method { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override string Scheme { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override bool IsHttps { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override HostString Host { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override PathString PathBase { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override PathString Path { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override QueryString QueryString { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override IQueryCollection Query { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override string Protocol { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }

        public override IHeaderDictionary Headers => _headers;

        public override IRequestCookieCollection Cookies { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override long? ContentLength { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override string ContentType { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }
        public override Stream Body { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }

        public override bool HasFormContentType => throw new System.NotImplementedException();

        public override IFormCollection Form { get => throw new System.NotImplementedException(); set => throw new System.NotImplementedException(); }

        public override Task<IFormCollection> ReadFormAsync(CancellationToken cancellationToken = default(CancellationToken))
        {
            throw new System.NotImplementedException();
        }
    }
}
