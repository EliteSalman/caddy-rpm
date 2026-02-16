%global debug_package %{nil}

Name:           caddy
Version:        2.10.2
Release:        6%{?dist}
Summary:        Web server with automatic HTTPS
License:        Apache-2.0
URL:            https://caddyserver.com
Packager:       Salman Shafi <hello@salmanshafi.net>

Source0:        https://raw.githubusercontent.com/caddyserver/caddy/v%{version}/cmd/caddy/main.go
Source10:       https://raw.githubusercontent.com/caddyserver/dist/master/config/Caddyfile
Source20:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy.service
Source21:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy-api.service
Source22:       https://raw.githubusercontent.com/caddyserver/dist/master/init/caddy.sysusers
Source30:       https://raw.githubusercontent.com/caddyserver/dist/master/welcome/index.html
Source90:       https://raw.githubusercontent.com/caddyserver/caddy/v%{version}/LICENSE

BuildRequires:  git-core
BuildRequires:  systemd-rpm-macros
BuildRequires:  brotli-devel
%{?systemd_requires}

BuildRequires:  golang >= 1.25

Provides:       webserver

%description
Caddy is an extensible server platform that uses TLS by default.
This build includes official DNS modules for Cloudflare and RFC2136,
plus additional modules: MaxMind geolocation, HTTP cache handler,
HTTP rate limiting, Layer 4 support, and Brotli compression support.

%prep
%setup -q -c -T
cp %{S:0} %{S:90} .

%build
%undefine _auto_set_build_flags

export GOPROXY='https://proxy.golang.org,direct'
export GOSUMDB='sum.golang.org'
export GOBIN=$(pwd)
export PATH=$PATH:$(pwd)

go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest

# Brotli support uses the reference Brotli C implementation
# Requires brotli-devel installed at build time
CGO_ENABLED=1 ./xcaddy build v%{version} \
    --with github.com/caddy-dns/cloudflare \
    --with github.com/caddy-dns/rfc2136 \
    --with github.com/porech/caddy-maxmind-geolocation \
    --with github.com/caddyserver/cache-handler \
    --with github.com/mholt/caddy-ratelimit \
    --with github.com/mholt/caddy-l4 \
    --with github.com/dunglas/caddy-cbrotli \
    --with github.com/WeidiDeng/caddy-cloudflare-ip \
    --output ./caddy

%install
install -D -p -m 0755 caddy %{buildroot}%{_bindir}/caddy

install -d -m 0755 %{buildroot}%{_mandir}/man8
./caddy manpage --directory %{buildroot}%{_mandir}/man8

install -D -p -m 0644 %{S:10} %{buildroot}%{_sysconfdir}/caddy/Caddyfile

install -D -p -m 0644 %{S:20} %{buildroot}%{_unitdir}/caddy.service
install -D -p -m 0644 %{S:21} %{buildroot}%{_unitdir}/caddy-api.service

install -D -p -m 0644 %{S:22} %{buildroot}%{_sysusersdir}/caddy.conf

install -d -m 0750 %{buildroot}%{_sharedstatedir}/caddy

install -D -p -m 0644 %{S:30} %{buildroot}%{_datadir}/caddy/index.html

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

if [ -x /usr/sbin/getsebool ]; then
    setsebool -P httpd_can_network_connect on
fi
if [ -x /usr/sbin/semanage -a -x /usr/sbin/restorecon ]; then
    semanage fcontext --add --type httpd_exec_t        '%{_bindir}/caddy'               2> /dev/null || :
    semanage fcontext --add --type httpd_sys_content_t '%{_datadir}/caddy(/.*)?'        2> /dev/null || :
    semanage fcontext --add --type httpd_config_t      '%{_sysconfdir}/caddy(/.*)?'     2> /dev/null || :
    semanage fcontext --add --type httpd_var_lib_t     '%{_sharedstatedir}/caddy(/.*)?' 2> /dev/null || :
    restorecon -r %{_bindir}/caddy %{_datadir}/caddy %{_sysconfdir}/caddy %{_sharedstatedir}/caddy || :
fi
if [ -x /usr/sbin/semanage ]; then
    semanage port --add --type http_port_t --proto udp 80   2> /dev/null || :
    semanage port --add --type http_port_t --proto udp 443  2> /dev/null || :
    semanage port --add --type http_port_t --proto tcp 2019 2> /dev/null || :
fi

%preun
%systemd_preun caddy.service

%postun
%systemd_postun_with_restart caddy.service

if [ $1 -eq 0 ]; then
    if [ -x /usr/sbin/getsebool ]; then
        setsebool -P httpd_can_network_connect off
    fi
    if [ -x /usr/sbin/semanage ]; then
        semanage fcontext --delete --type httpd_exec_t        '%{_bindir}/caddy'               2> /dev/null || :
        semanage fcontext --delete --type httpd_sys_content_t '%{_datadir}/caddy(/.*)?'        2> /dev/null || :
        semanage fcontext --delete --type httpd_config_t      '%{_sysconfdir}/caddy(/.*)?'     2> /dev/null || :
        semanage fcontext --delete --type httpd_var_lib_t     '%{_sharedstatedir}/caddy(/.*)?' 2> /dev/null || :
        semanage port     --delete --type http_port_t --proto udp 80   2> /dev/null || :
        semanage port     --delete --type http_port_t --proto udp 443  2> /dev/null || :
        semanage port     --delete --type http_port_t --proto tcp 2019 2> /dev/null || :
    fi
fi

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
* Sat Feb 07 2026 Salman Shafi <hello@salmanshafi.net> - 2.10.2-5
- Added Brotli compression support (caddy-cbrotli module).

* Sat Feb 07 2026 Salman Shafi <hello@salmanshafi.net> - 2.10.2-4
- Added extra modules: MaxMind geolocation, HTTP cache handler, HTTP rate limiting, and Layer 4 support.

* Fri Feb 06 2026 Salman Shafi <hello@salmanshafi.net> - 2.10.2-3
- Added official DNS modules: Cloudflare & RFC2136