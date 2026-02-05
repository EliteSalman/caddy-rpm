%global debug_package %{nil}

Name:           caddy
Version:        2.10.2
Release:        2%{?dist}
Summary:        Web server with automatic HTTPS & Additional DNS Modules
License:        Apache-2.0
URL:            https://caddyserver.com
Packager:       Salman Shafi <hello@salmanshafi.net>

# In order to build Caddy with version information, we need to import it as a
# go module.  To do that, we are going to forgo the traditional source tarball
# and instead use just this file from upstream.  This method requires that we
# allow networking in the build environment.
Source0:        https://raw.githubusercontent.com/caddyserver/caddy/v%{version}/cmd/caddy/main.go

# Use official resources for config, unit file, and welcome page.
Source10:       https://raw.githubusercontent.com/caddyserver/dist/master/config/Caddyfile
Source20:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy.service
Source21:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy-api.service
Source22:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy.sysusers
Source30:       https://raw.githubusercontent.com/caddyserver/dist/master/welcome/index.html

# Since we are not using a traditional source tarball, we need to explicitly
# pull in the license file.
Source90:       https://raw.githubusercontent.com/caddyserver/caddy/v%{version}/LICENSE

BuildRequires:  git-core
BuildRequires:  systemd
BuildRequires:  systemd-rpm-macros
%{?systemd_requires}

# BuildRequires for Go (xcaddy will be installed at build time)
BuildRequires:  golang

Provides:       webserver

%description
Caddy is a fast, extensible web server with automatic HTTPS support.
This package produces a Caddy binary that includes support for
Cloudflare and RFC2136 DNS providers for ACME DNS-01 challenge validation.

%prep
%setup -q -c -T
# Copy main.go and LICENSE into the build directory.
cp %{S:0} %{S:90} .

%build
# Allow Go proxy for dependency resolution
export GOPROXY='https://proxy.golang.org,direct'
export GOSUMDB='sum.golang.org'

# Build xcaddy locally so we can embed plugins without requiring an xcaddy RPM
go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest
export PATH=$PATH:$(go env GOPATH)/bin

# Now build Caddy with Cloudflare & RFC2136 DNS modules
xcaddy build v%{version} \
    --with github.com/caddy-dns/cloudflare \
    --with git.rokan.xyz/aber/caddy-dns-rfc2136

%install
# command
install -D -p -m 0755 caddy %{buildroot}%{_bindir}/caddy

# man pages
./caddy manpage --directory %{buildroot}%{_mandir}/man8

# config
install -D -p -m 0644 %{S:10} %{buildroot}%{_sysconfdir}/caddy/Caddyfile

# systemd units
install -D -p -m 0644 %{S:20} %{buildroot}%{_unitdir}/caddy.service
install -D -p -m 0644 %{S:21} %{buildroot}%{_unitdir}/caddy-api.service

# sysusers
install -D -p -m 0644 %{S:22} %{buildroot}%{_sysusersdir}/caddy.conf

# data directory
install -d -m 0750 %{buildroot}%{_sharedstatedir}/caddy

# welcome page
install -D -p -m 0644 %{S:30} %{buildroot}%{_datadir}/caddy/index.html

# shell completions
install -d -m 0755 %{buildroot}%{_datadir}/bash-completion/completions
./caddy completion bash > %{buildroot}%{_datadir}/bash-completion/completions/caddy
install -d -m 0755 %{buildroot}%{_datadir}/zsh/site-functions
./caddy completion zsh > %{buildroot}%{_datadir}/zsh/site-functions/_caddy
install -d -m 0755 %{buildroot}%{_datadir}/fish/vendor_completions.d
./caddy completion fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/caddy.fish

%pre
%if 0%{?el7}
%sysusers_create_compat %{S:22}
%else
%sysusers_create_package %{name} %{S:22}
%endif

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
