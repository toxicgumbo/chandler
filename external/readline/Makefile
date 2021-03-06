
include ../Makefile.inc

VERSION=5.0
RELVER=$(VERSION)-1
BUILD=build_$(SNAP)
READLINE=$(BUILD_ROOT)/readline
SRC=$(READLINE)/$(BUILD)
SRC_BUILD=$(SRC)/readline-$(VERSION)  

.PHONY: readline

ifeq ($(OS),Darwin)

$(SRC)/Makefile:
	cd $(SRC_BUILD); \
	./configure --prefix=$(PREFIX)

readline: $(SRC)/Makefile apply
	$(MAKE) -C $(SRC_BUILD)
	$(MAKE) -C $(SRC_BUILD) install

clean:
	rm -rf $(READLINE)/$(BUILD)
	rm -f $(READLINE)/readline-$(VERSION)-$(SNAP)-expanded

ifeq ($(strip $(OS_VERSION)),8.0.0) 
apply:
	mv $(SRC_BUILD)/shlib/Makefile $(SRC_BUILD)/shlib/Makefile.backup
	sed -e 's/-dynamic /-dynamiclib /' $(SRC_BUILD)/shlib/Makefile.backup > $(SRC_BUILD)/shlib/Makefile
else
# Nothing to do
apply:
endif 

snap:
	cd $(BUILD_ROOT); \
        tar -cvzf $(READLINE)/readline-$(SNAP)-$(RELVER).tar.gz \
        $(SNAP)/lib/libreadline* --exclude '*.a'; \
	$(MD5) $(READLINE)/readline-$(SNAP)-$(RELVER).tar.gz > $(READLINE)/readline-$(SNAP)-$(RELVER).tar.gz.md5   

upload: readline-$(SNAP)-$(RELVER).tar.gz
	scp readline-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp readline-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install: readline-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf readline-$(SNAP)-$(RELVER).tar.gz

readline-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/readline-$(VERSION).tar.gz 
	$(CURL) http://builds.o11n.org/external/readline-$(VERSION).tar.gz.md5

sources: readline-$(VERSION).tar.gz

readline-$(VERSION)-$(SNAP)-expanded: readline-$(VERSION).tar.gz
	mkdir -p $(READLINE)/$(BUILD)
	tar -C $(READLINE)/$(BUILD) -xzf $(READLINE)/readline-$(VERSION).tar.gz
	touch $(READLINE)/readline-$(VERSION)-$(SNAP)-expanded

expand: readline-$(VERSION)-$(SNAP)-expanded

else

  # Nothing to do
readline:

  # Nothing to do
clean:

  # Nothing to do
snap:

  # Nothing to do
upload:

  # Nothing to do
install:

  # Nothing to do
sources:

  # Nothing to do
expand:

endif

build: expand readline

