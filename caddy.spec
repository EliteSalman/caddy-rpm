%global debug_package %{nil}

Name:           caddy
Version:        2.10.2
Release:        2%{?dist}
Summary:        Web server with automatic HTTPS
License:        Apache-2.0
URL:            https://caddyserver.com
Packager:       Salman Shafi <hello@salmanshafi.net>

# Source URLs
Source0:        https://raw.githubusercontent.com/caddyserver/caddy/v%{version}/cmd/caddy/main.go
Source10:       https://raw.githubusercontent.com/caddyserver/dist/master/config/Caddyfile
Source20:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy.service
Source21:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy-api.service
Source22:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy.sysusers
Source30:       https://raw.githubusercontent.com/caddyserver/dist/master/welcome/index.html
Source90:       https://raw.githubusercontent.com/caddyserver/caddy/v%{version}/LICENSE

BuildRequires:  git-core
BuildRequires:  systemd
BuildRequires:  systemd-rpm-macros
%{?systemd_requires}
BuildRequires:  golang >= 1.25

Provides:       webserver

%description
Caddy is a fast, extensible web server with automatic HTTPS support. 
This build includes support for Cloudflare and RFC2136 DNS providers.

%prep
%setup -q -c -T
cp %{S:0} %{S:90} .

%build
export GOPROXY='https://proxy.golang.org,direct'
go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest
export PATH=$PATH:$(go env GOPATH)/bin

# Build with Official Caddy-DNS Modules
xcaddy build v%{version} \
    --with github.com/caddy-dns/cloudflare \
    --with github.com/caddy-dns/rfc2136

%install
install -D -p -m 0755 caddy %{buildroot}%{_bindir}/caddy
./caddy manpage --directory %{buildroot}%{_mandir}/man8
install -D -p -m 0644 %{S:10} %{buildroot}%{_sysconfdir}/caddy/Caddyfile
install -D -p -m 0644 %{S:20} %{buildroot}%{_unitdir}/caddy.service
install -D -p -m 0644 %{S:21} %{buildroot}%{_unitdir}/caddy-api.service
install -D -p -m 0644 %{S:22} %{buildroot}%{_sysusersdir}/caddy.conf
install -d -m 0750 %{buildroot}%{_sharedstatedir}/caddy
install -D -p -m 0644 %{S:30} %{buildroot}%{_datadir}/caddy/index.html

# Shell completions
install -d -m 0755 %{buildroot}%{_datadir}/bash-completion/completions
./caddy completion bash > %{buildroot}%{_datadir}/bash-completion/completions/caddy
install -d -m 0755 %{buildroot}%{_datadir}/zsh/site-functions
./caddy completion zsh > %{buildroot}%{_datadir}/zsh/site-functions/_caddy
install -d -m 0755 %{buildroot}%{_datadir}/fish/vendor_completions.d
./caddy completion fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/caddy.fish

%pre
%sysusers_create_package %{name} %{S:22}

%post
%systemd_post caddy.service

%preun
%systemd_preun caddy.service

%postun
%systemd_postun_with_restart caddy.service

%files
%license LICENSE
%{_bindir}/caddy
%{_mandir}/man8/caddy*.8*
%{_datadir}/caddy
%{_unitdir}/caddy.service
%{_unitdir}/caddy-api.service
%{_sysusersdir}/caddy.conf
%dir %{_sysconfdir}/caddy
%config(noreplace) %{_sysconfdir}/caddy/Caddyfile
%attr(0750,caddy,caddy) %dir %{_sharedstatedir}/caddy
%{_datadir}/bash-completion/completions/caddy
%{_datadir}/zsh/site-functions/_caddy
%{_datadir}/fish/vendor_completions.d/caddy.fish

%changelog
* Fri Feb 06 2026 Salman Shafi <hello@salmanshafi.net> - 2.10.2-2
- CloudFlare & RFC2136 DNS Module added
